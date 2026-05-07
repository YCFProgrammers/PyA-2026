import asyncio
import logging
import os
import re
import time
from collections import defaultdict, deque
from datetime import timedelta, datetime, timezone

import discord
import discord.utils
from discord import app_commands
from discord.ext import commands, tasks

import db

log = logging.getLogger(__name__)

# Spam tracking registry { user_id: [timestamps] }
_spam_tracker: dict[int, list[float]] = defaultdict(list)
# Joins recientes para anti-raid: deque de timestamps
_recent_joins: deque[float] = deque(maxlen=50)

SPAM_LIMIT        = 7     # max messages in window (subido para evitar warnear chat normal)
SPAM_WINDOW       = 6.0   # seconds of the window
SPAM_MUTE_TIME    = 300   # mute duration in seconds (5 minutes)
SPAM_MAX_CHARS    = 200   # max characters per message
SPAM_TRACKER_TTL  = 300   # seg sin actividad → purgar entrada del tracker

RAID_JOIN_LIMIT   = 5     # joins en RAID_JOIN_WINDOW para gatillar alerta
RAID_JOIN_WINDOW  = 60.0
WARN_LIMIT_KICK   = 3     # warnings → kick automático

VOWELS = "aáéíóúoe"
MENTION_RE = re.compile(r"<[@#!&][0-9]+>")
# emojis custom de Discord <:name:id> y <a:name:id>
CUSTOM_EMOJI_RE = re.compile(r"<a?:[A-Za-z0-9_]+:[0-9]+>")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
REPEATED_CHAR_RE = re.compile(r"([a-záéíóúñ])\1{4,}")
# unicode emoji range aproximado (BMP + suplementarios comunes)
UNICODE_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]",
    flags=re.UNICODE,
)
# invites de otros servidores Discord
INVITE_RE = re.compile(r"(?:discord\.gg|discord(?:app)?\.com/invite)/[\w-]+", re.IGNORECASE)


def _env_id(name: str) -> int | None:
    v = os.getenv(name)
    try:
        return int(v) if v else None
    except ValueError:
        return None


def _env_id_set(name: str) -> set[int]:
    v = os.getenv(name, "")
    out: set[int] = set()
    for chunk in v.split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            out.add(int(chunk))
    return out


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.mod_log_channel_id = _env_id("MOD_LOG_CHANNEL_ID")
        self.whitelist_channels = _env_id_set("MOD_WHITELIST_CHANNELS")
        self.whitelist_roles = _env_id_set("MOD_WHITELIST_ROLES")

    async def cog_load(self) -> None:
        await db.init()
        self.purge_tracker.start()

    async def cog_unload(self) -> None:
        self.purge_tracker.cancel()

    # ----- helpers -----

    def _is_whitelisted(self, message: discord.Message) -> bool:
        if message.channel.id in self.whitelist_channels:
            return True
        if isinstance(message.author, discord.Member):
            user_role_ids = {r.id for r in message.author.roles}
            if user_role_ids & self.whitelist_roles:
                return True
        return False

    async def _mod_log(self, guild: discord.Guild | None, embed: discord.Embed) -> None:
        if not guild or not self.mod_log_channel_id:
            return
        channel = guild.get_channel(self.mod_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(embed=embed)
            except discord.HTTPException as e:
                log.warning("mod log send failed: %s", e)

    async def _mute(self, member: discord.Member, seconds: int, reason: str) -> None:
        # timeout nativo de Discord
        try:
            await member.timeout(timedelta(seconds=seconds), reason=reason)
        except discord.Forbidden:
            log.warning("missing perms to timeout %s", member)
        except discord.HTTPException as e:
            log.warning("timeout failed for %s: %s", member, e)

    # ----- spam detection -----

    def is_spam(self, message: discord.Message) -> tuple[bool, str]:
        """
        Detecta si un mensaje es spam.
        Returns (is_spam: bool, reason: str)
        """
        guild = message.guild
        content = message.content

        # Remover menciones, emojis custom, emojis unicode y URLs antes de analizar
        # (gifts/stickers/links no deben gatillar spam por baja proporción de vocales)
        text_clean = MENTION_RE.sub("", content)
        text_clean = CUSTOM_EMOJI_RE.sub("", text_clean)
        text_clean = UNICODE_EMOJI_RE.sub("", text_clean)
        text_clean = URL_RE.sub("", text_clean)
        text_lower = text_clean.lower()
        words = text_lower.split()

        # Si tras limpiar no queda contenido relevante, no analizar
        if not text_lower.strip():
            return False, ""

        # Check 1: más de 5 letras consecutivas iguales
        if REPEATED_CHAR_RE.search(text_lower):
            return True, "Spam detectado: caracteres repetidos excesivamente"

        # Check 2: palabras repetidas más de 3 veces
        clean_words = [re.sub(r"[^\w]", "", w) for w in words]
        clean_words = [w for w in clean_words if w]

        word_count: dict[str, int] = {}
        for word in clean_words:
            word_count[word] = word_count.get(word, 0) + 1
            if word_count[word] > 3:
                return True, f"Spam detectado: palabra '{word}' repetida {word_count[word]} veces"

        # Check 3: palabras sin sentido (pocas vocales)
        # cachear nombres del guild una vez (evita lookup O(n) por palabra)
        if guild is not None:
            member_names = {m.name.lower() for m in guild.members}
            role_names = {r.name.lower() for r in guild.roles}
            channel_names = {c.name.lower() for c in guild.channels}
        else:
            member_names = role_names = channel_names = set()

        for word in clean_words:
            # subido a 15 para evitar matchear identificadores legítimos
            if len(word) <= 15:
                continue

            # Solo letras: si la palabra tiene dígitos es probablemente un ID/slug
            if not word.isalpha():
                continue

            # Ignorar si coincide con nombre de miembro
            if word in member_names:
                continue
            # Ignorar si coincide con nombre de rol
            if word in role_names:
                continue
            # Ignorar si coincide con nombre de canal
            if word in channel_names:
                continue

            vowel_count = sum(1 for letter in word if letter in VOWELS)
            vowel_percentage = (vowel_count / len(word)) * 100
            # bajado a 15% para reducir falsos positivos
            if vowel_percentage < 15:
                return True, f"Spam detectado: cadena sin sentido '{word}'"

        return False, ""

    def has_alternating_caps(self, message: str) -> bool:
        """
        Detects if the message has alternating CAPS between words.
        Example: "HOLA mundo ESTO es TEST" → True
        """
        # Ignorar URLs y emojis custom para que no cuenten como palabras
        cleaned = URL_RE.sub("", message)
        cleaned = CUSTOM_EMOJI_RE.sub("", cleaned)
        words = cleaned.split()
        if len(words) < 2:
            return False

        upper_count = 0
        lower_count = 0

        for word in words:
            clean_word = re.sub(r"[^\w]", "", word)
            if not clean_word:
                continue
            if clean_word.isupper():
                upper_count += 1
            elif clean_word.islower():
                lower_count += 1

        return upper_count > 1 and lower_count > 1

    # ----- listeners -----

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Unified listener that detects and removes spam messages
        """
        # Ignore bots
        if message.author.bot:
            return

        # DM o webhooks no tienen Member
        if not isinstance(message.author, discord.Member):
            return

        # Ignore administrators
        if message.author.guild_permissions.administrator:
            return

        # Whitelist (canales o roles configurados via env)
        if self._is_whitelisted(message):
            return

        # Stickers/attachments/embeds-only: no analizar (gifs, gifts, imágenes)
        if not message.content.strip() and (
            message.stickers or message.attachments or message.embeds
        ):
            return

        # Filtro de invites a otros servidores
        if INVITE_RE.search(message.content):
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            embed = discord.Embed(
                title="🔗 Invite removida",
                description="No se permiten invites a otros servidores.",
                color=discord.Color.red(),
            )
            await message.channel.send(content=message.author.mention, embed=embed, delete_after=10)
            return

        # # Check 1: Message length (max 200 characters)
        # if len(message.content) > SPAM_MAX_CHARS:
        #     try:
        #         await message.delete()
        #         await message.channel.send(
        #             f"⚠️ {message.author.mention} tu mensaje supera los **{SPAM_MAX_CHARS} caracteres**.",
        #             delete_after=5
        #         )
        #     except Exception as e:
        #         print(f"Error validating length: {e}")
        #     return

        # Check 2: Frequency anti-spam
        user_id = message.author.id
        now = time.time()

        _spam_tracker[user_id] = [
            t for t in _spam_tracker[user_id]
            if now - t < SPAM_WINDOW
        ]
        _spam_tracker[user_id].append(now)

        if len(_spam_tracker[user_id]) >= SPAM_LIMIT:
            _spam_tracker[user_id].clear()
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            # mute por SPAM_MUTE_TIME
            await self._mute(message.author, SPAM_MUTE_TIME, "Spam por frecuencia")
            embed = discord.Embed(
                title="⏱️ Spam por frecuencia detectado",
                description=f"Estás enviando mensajes demasiado rápido. Silenciado por {SPAM_MUTE_TIME // 60} minutos.",
                color=discord.Color.orange()
            )
            await message.channel.send(
                content=f"{message.author.mention}",
                embed=embed,
                delete_after=10
            )
            await self._mod_log(
                message.guild,
                discord.Embed(
                    title="Auto-mute (spam frecuencia)",
                    description=f"{message.author.mention} silenciado {SPAM_MUTE_TIME // 60}min",
                    color=discord.Color.orange(),
                ),
            )
            return

        # Check 3: Detect alternating CAPS
        if self.has_alternating_caps(message.content):
            try:
                lowered_message = message.content.lower()
                await message.delete()

                embed = discord.Embed(
                    description=lowered_message,
                    color=discord.Color.blue()
                )
                embed.set_author(
                    name=message.author.name,
                    icon_url=message.author.avatar.url if message.author.avatar else None
                )
                embed.set_footer(text="Mensaje corregido de MAYÚSCULAS a minúsculas")

                await message.channel.send(embed=embed)
            except discord.HTTPException as e:
                log.warning("alternating caps handling failed: %s", e)
            return

        # Check 4: Detect regular spam (repeated words, repeated chars, etc)
        # fix: pasar message completo, no (content, guild)
        spam_detected, reason = self.is_spam(message)

        if spam_detected:
            try:
                await message.delete()
                embed = discord.Embed(
                    title="⚠️ Mensaje eliminado por spam",
                    description=reason,
                    color=discord.Color.red()
                )
                embed.set_footer(text="Por favor, sé respetuoso con el chat")
                await message.channel.send(
                    content=f"{message.author.mention}",
                    embed=embed,
                    delete_after=10
                )
            except discord.HTTPException as e:
                log.warning("spam delete failed: %s", e)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # anti-raid: detectar joins masivos
        now = time.time()
        _recent_joins.append(now)
        recientes = [t for t in _recent_joins if now - t < RAID_JOIN_WINDOW]
        if len(recientes) >= RAID_JOIN_LIMIT:
            embed = discord.Embed(
                title="🚨 Posible raid detectado",
                description=f"{len(recientes)} joins en {int(RAID_JOIN_WINDOW)}s",
                color=discord.Color.red(),
            )
            await self._mod_log(member.guild, embed)

    # ----- task purge -----

    @tasks.loop(minutes=5)
    async def purge_tracker(self):
        now = time.time()
        stale = [uid for uid, ts in _spam_tracker.items() if not ts or now - ts[-1] > SPAM_TRACKER_TTL]
        for uid in stale:
            _spam_tracker.pop(uid, None)

    @purge_tracker.before_loop
    async def before_purge(self):
        await self.bot.wait_until_ready()

    # ----- comandos -----

    @commands.hybrid_command(name="anuncio", description="Crea un anuncio con mención a todos")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)  # max 1 anuncio/min por guild
    async def anuncio(self, ctx: commands.Context, titulo: str, *, mensaje: str):
        embed = discord.Embed(
            title=f"📢 {titulo}",
            description=mensaje,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Enviado por: {ctx.author.name}")
        embed.timestamp = ctx.message.created_at if ctx.message else discord.utils.utcnow()

        # allowed_mentions explicito para que @everyone realmente pingee
        await ctx.send(
            content="@everyone",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True),
        )

        if ctx.message:
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass

    @commands.hybrid_command(name="kick", description="Expulsa a un usuario")
    @commands.has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "Sin razón"
    ):
        await member.kick(reason=reason)
        await ctx.send(f'👢 {member.mention} ha sido expulsado.')
        await self._mod_log(
            ctx.guild,
            discord.Embed(
                title="Kick",
                description=f"{member.mention} por {ctx.author.mention}\nRazón: {reason}",
                color=discord.Color.orange(),
            ),
        )

    @commands.hybrid_command(name="ban", description="Banea a un usuario permanentemente")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="Usuario", reason="Razón", confirm="Escribe SI para confirmar")
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        confirm: str = "",
        *,
        reason: str = "Sin razón"
    ):
        # ban temporal real no existe en Discord; ver -mute para silencio temporal
        if confirm.upper() != "SI":
            await ctx.send(
                f"⚠️ Confirma el ban permanente de {member.mention} repitiendo el comando con `confirm: SI`."
            )
            return
        await member.ban(reason=reason)
        await ctx.send(f'🔨 {member.mention} ha sido baneado **permanentemente**.')
        await self._mod_log(
            ctx.guild,
            discord.Embed(
                title="Ban",
                description=f"{member.mention} por {ctx.author.mention}\nRazón: {reason}",
                color=discord.Color.red(),
            ),
        )

    @commands.hybrid_command(name="mute", description="Silencia a un usuario por tiempo determinado")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(
        member="Usuario a silenciar",
        timetype="Unidad de tiempo",
        amount="Cantidad",
        reason="Razón"
    )
    @app_commands.choices(timetype=[
        app_commands.Choice(name="Segundos", value="seconds"),
        app_commands.Choice(name="Minutos", value="minutes"),
        app_commands.Choice(name="Horas", value="hours"),
    ])
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        timetype: str = "minutes",
        amount: int = 5,
        *,
        reason: str = "Sin razón"
    ):
        if isinstance(timetype, app_commands.Choice):
            timetype = timetype.value

        seconds = amount
        if timetype == "minutes":
            seconds *= 60
        elif timetype == "hours":
            seconds *= 3600

        if seconds <= 0:
            await ctx.send("Duración inválida.")
            return

        await member.timeout(timedelta(seconds=seconds), reason=reason)
        await ctx.send(f'🔇 {member.mention} silenciado por **{seconds} segundos**.')
        await self._mod_log(
            ctx.guild,
            discord.Embed(
                title="Mute",
                description=f"{member.mention} {seconds}s por {ctx.author.mention}\nRazón: {reason}",
                color=discord.Color.orange(),
            ),
        )

    @commands.hybrid_command(name="warn", description="Da una advertencia a un usuario")
    @commands.has_permissions(moderate_members=True)
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "Sin razón"
    ):
        if ctx.guild is None:
            return
        total = await db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        embed = discord.Embed(
            title="⚠️ Advertencia registrada",
            description=f"{member.mention} ({total}/{WARN_LIMIT_KICK}) — {reason}",
            color=discord.Color.yellow(),
        )
        await ctx.send(embed=embed)
        await self._mod_log(ctx.guild, embed)

        if total >= WARN_LIMIT_KICK:
            try:
                await member.kick(reason=f"Acumuló {total} warnings")
                await ctx.send(f"👢 {member.mention} expulsado por acumular {total} warnings.")
            except discord.Forbidden:
                await ctx.send("No tengo permisos para expulsar a ese usuario.")

    @commands.hybrid_command(name="warnings", description="Lista warnings de un usuario")
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        if ctx.guild is None:
            return
        rows = await db.get_warnings(ctx.guild.id, member.id)
        if not rows:
            await ctx.send(f"✅ {member.mention} no tiene warnings.")
            return
        embed = discord.Embed(
            title=f"Warnings de {member.display_name}",
            color=discord.Color.yellow(),
        )
        for wid, mod_id, reason, created in rows[:10]:
            embed.add_field(
                name=f"#{wid} • {created}",
                value=f"Por <@{mod_id}>: {reason or 'Sin razón'}",
                inline=False,
            )
        embed.set_footer(text=f"Total: {len(rows)}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarns", description="Borra todos los warnings de un usuario")
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx: commands.Context, member: discord.Member):
        if ctx.guild is None:
            return
        n = await db.clear_warnings(ctx.guild.id, member.id)
        await ctx.send(f"🧹 {n} warnings eliminados de {member.mention}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
