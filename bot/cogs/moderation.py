import discord
from discord import app_commands
from discord.ext import commands
from collections import defaultdict
import discord.utils
import re
import time

# Spam tracking registry { user_id: [timestamps] }
_spam_tracker: dict[int, list[float]] = defaultdict(list)

SPAM_LIMIT        = 5     # max messages in window
SPAM_WINDOW       = 5.0   # seconds of the window
SPAM_MUTE_TIME    = 300   # mute duration in seconds (5 minutes)
SPAM_MAX_CHARS    = 200   # max characters per message

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

        # Extraer IDs de menciones reales del mensaje
        mentioned_user_ids = {m.id for m in message.mentions}
        mentioned_role_ids = {r.id for r in message.role_mentions}

        # Remover menciones del texto antes de analizar
        text_clean = re.sub(r'<[@#!&][0-9]+>', '', content)
        text_lower = text_clean.lower()
        words = text_lower.split()

        # Check 1: más de 5 letras consecutivas iguales
        if re.search(r'([a-záéíóúñ])\1{4,}', text_lower):
            return True, "Spam detectado: caracteres repetidos excesivamente"

        # Check 2: palabras repetidas más de 3 veces
        clean_words = [re.sub(r'[^\w]', '', w) for w in words]
        clean_words = [w for w in clean_words if w]

        word_count = {}
        for word in clean_words:
            word_count[word] = word_count.get(word, 0) + 1

        for word, count in word_count.items():
            if count > 3:
                return True, f"Spam detectado: palabra '{word}' repetida {count} veces"

        # Check 3: palabras sin sentido (pocas vocales)
        vowels = 'aáéíóúoe'
        for word in clean_words:
            if len(word) <= 10:
                continue

            # Ignorar si coincide con nombre de miembro
            if guild.get_member_named(word):
                continue

            # Ignorar si coincide con nombre de rol
            if discord.utils.get(guild.roles, name=word):
                continue

            # Ignorar si coincide con nombre de canal
            if discord.utils.get(guild.channels, name=word):
                continue

            vowel_count = sum(1 for letter in word if letter in vowels)
            vowel_percentage = (vowel_count / len(word)) * 100
            if vowel_percentage < 20:
                return True, f"Spam detectado: cadena sin sentido '{word}'"

        return False, ""

    def has_alternating_caps(self, message: str) -> bool:
        """
        Detects if the message has alternating CAPS between words.
        Example: "HOLA mundo ESTO es TEST" → True
        """
        words = message.split()
        if len(words) < 2:
            return False

        upper_count = 0
        lower_count = 0

        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
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

        # Ignore administrators
        if message.author.guild_permissions.administrator:
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

        # Check 2: Frequency anti-spam (max 5 messages in 5 seconds)
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
                embed = discord.Embed(
                    title="⏱️ Spam por frecuencia detectado",
                    description="Estás enviando mensajes demasiado rápido. Silenciado por 5 minutos.",
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
        spam_detected, reason = self.is_spam(message.content, message.guild)

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