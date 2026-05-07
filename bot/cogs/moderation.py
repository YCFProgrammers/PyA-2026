import discord
from discord import app_commands
from discord.ext import commands
from collections import defaultdict
import discord.utils
import re
import time
from datetime import timedelta

# Spam tracking registry { user_id: [timestamps] }
_spam_tracker: dict[int, list[float]] = defaultdict(list)

SPAM_LIMIT        = 7     # max messages in window (subido para evitar warnear chat normal)
SPAM_WINDOW       = 6.0   # seconds of the window
SPAM_MUTE_TIME    = 300   # mute duration in seconds (5 minutes)
SPAM_MAX_CHARS    = 200   # max characters per message

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


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

        # Stickers/attachments/embeds-only: no analizar (gifs, gifts, imágenes)
        if not message.content.strip() and (
            message.stickers or message.attachments or message.embeds
        ):
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
                # aplicar timeout real (antes solo decía "silenciado" pero no muteaba)
                try:
                    await message.author.timeout(
                        timedelta(seconds=SPAM_MUTE_TIME),
                        reason="Spam por frecuencia",
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
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
            except Exception as e:
                print(f"Error handling frequency spam: {e}")
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
            except Exception as e:
                print(f"Error correcting alternating caps: {e}")
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
            except Exception as e:
                print(f"Error deleting spam message: {e}")


    @commands.hybrid_command(name="anuncio", description="Crea un anuncio con mención a todos")
    @commands.has_permissions(administrator=True)
    async def anuncio(self, ctx: commands.Context, titulo: str, *, mensaje: str):
        embed = discord.Embed(
            title=f"📢 {titulo}",
            description=mensaje,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Enviado por: {ctx.author.name}")
        embed.timestamp = ctx.message.created_at if ctx.message else discord.utils.utcnow()

        await ctx.send(content="@everyone", embed=embed)

        if ctx.message:
            await ctx.message.delete()


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


    @commands.hybrid_command(name="ban", description="Banea a un usuario con duración opcional")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        member="Usuario a banear",
        timetype="Tipo de tiempo",
        timeparams="Cantidad de tiempo",
        reason="Razón del ban"
    )
    @app_commands.choices(timetype=[
        app_commands.Choice(name="Segundos", value="seconds"),
        app_commands.Choice(name="Minutos", value="minutes"),
        app_commands.Choice(name="Horas", value="hours"),
    ])
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        timetype: str | None = None,
        timeparams: int = 0,
        *,
        reason: str = "Sin razón"
    ):
        if isinstance(timetype, app_commands.Choice):
            timetype = timetype.value
        elif timetype is None:
            timetype = "seconds"

        duration = timeparams
        if timetype == "hours":
            duration *= 3600
        elif timetype == "minutes":
            duration *= 60

        await member.ban(reason=reason)

        if duration > 0:
            await ctx.send(f'🔨 {member.mention} ha sido baneado por **{duration} segundos**.')
        else:
            await ctx.send(f'🔨 {member.mention} ha sido baneado **permanentemente**.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
