import logging
import os

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

# Anthropic es opcional; si no está la lib o la API key, el comando responde con aviso
try:
    from anthropic import AsyncAnthropic  # type: ignore
    _HAS_ANTHROPIC = True
except ImportError:
    AsyncAnthropic = None  # type: ignore
    _HAS_ANTHROPIC = False


SYSTEM_PROMPT = (
    "Eres un asistente experto en programación Python. "
    "Responde de forma concisa y con ejemplos cuando ayuden. Máximo 1500 caracteres."
)


class Consults(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if _HAS_ANTHROPIC and api_key:
            self._client = AsyncAnthropic(api_key=api_key)
        else:
            log.info("Anthropic deshabilitado (lib o API key faltante)")

    @commands.hybrid_command(name="ask", description="Pregunta a la IA")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ask(self, ctx: commands.Context, *, pregunta: str):
        if self._client is None:
            await ctx.send("⚠️ IA no configurada. Falta `ANTHROPIC_API_KEY` o la librería `anthropic`.")
            return

        await ctx.defer()
        try:
            response = await self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=800,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": pregunta}],
            )
            # extraer texto del primer bloque
            texto = ""
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    texto += block.text
            texto = texto.strip() or "(respuesta vacía)"
            if len(texto) > 1900:
                texto = texto[:1900] + "..."

            embed = discord.Embed(
                title="🤖 Respuesta IA",
                description=texto,
                color=discord.Color.teal(),
            )
            embed.set_footer(text=f"Pregunta de {ctx.author.display_name}")
            await ctx.send(embed=embed)
        except Exception as e:
            log.error("ask failed: %s", e)
            await ctx.send(f"❌ Error consultando IA: {e}")


async def setup(bot):
    await bot.add_cog(Consults(bot))
