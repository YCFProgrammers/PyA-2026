import discord
import aiohttp
import random
import json
import re

from datetime import datetime
from discord.ext import commands
from deep_translator import GoogleTranslator

# ---- Llamar al exercise.json ----
with open("exercises.json", "r", encoding="utf-8") as f:
    KATAS = json.load(f)

# ---- Colores por dificultad ----
COLORES = {
    "8kyu": discord.Color.light_grey(),
    "7kyu": discord.Color.blue(),
    "6kyu": discord.Color.yellow(),
    "5kyu": discord.Color.purple(),
    "4kyu": discord.Color.dark_blue(),
    "3kyu": discord.Color.red(),
    "2kyu": discord.Color.dark_red(),
    "1kyu": discord.Color.og_blurple(),
}

# ---- Helper de traducción ----


def traducir(texto: str) -> str:
    try:
        # Eliminar bloques de lenguajes específicos irrelevantes
        texto = re.sub(r'```(?!python\b)\w+[\s\S]*?```', '', texto)
        
        # Limpiar tildes sueltas que quedan (evita tachado en Discord)
        texto = re.sub(r'~~+', '', texto)
        
        # Separar bloques de código restantes del texto normal
        partes = re.split(r'(```[\s\S]*?```|`[^`\n]+`)', texto)
        resultado = []
        for parte in partes:
            if parte.startswith('`'):
                resultado.append(parte)
            elif parte.strip():
                traducido = GoogleTranslator(source='auto', target='es').translate(parte[:4999])
                resultado.append(traducido)
            else:
                resultado.append(parte)
        return ''.join(resultado)
    except Exception:
        return texto


# ---- Helper ----
async def _fetch_kata(slug: str) -> dict | None:
    url = f"https://www.codewars.com/api/v1/code-challenges/{slug}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            print(response.status)
            if response.status == 200:
                return await response.json()
            return None


# ---- Clase ----
class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="exercise", description="Devuelve un ejercicio de dificultad dada del 1(dificil) al 8(facil), de la pagina codewars")
    async def exercise(self, ctx: commands.Context, difficulty: int = 8):
        if difficulty is None:
            embed = discord.Embed(
                title="Ejercicio diario — Codewars",
                description="Elige una difficulty:",
                color=discord.Color.orange()
            )
            for level, katas in KATAS.items():
                embed.add_field(
                    name=level,
                    value=f"{len(katas)} katas disponibles",
                    inline=True
                )
            embed.set_footer(text="Uso: -exercise <difficulty>  •  Ej: -exercise 6")
            await ctx.send(embed=embed)
            return

        # Validar difficulty
        key = (str(difficulty) + 'kyu').lower()
        if key not in KATAS:
            embed = discord.Embed(
                title="Dificultad no valida",
                description=f"`{difficulty}` no existe.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Opciones validas",
                value=" • ".join(f"`{k}`" for k in range(1, 9)),
                inline=False
            )
            await ctx.send(embed=embed)
            return

        # Defer para evitar timeout mientras se traduce
        await ctx.defer()

        # Seleccionar kata aleatorio y llamar a la API
        slug = random.choice(KATAS[key])
        kata = await _fetch_kata(slug)

        if kata is None:
            await ctx.send("No se pudo obtener el kata, intenta de nuevo.")
            return

        # Traducir nombre y descripción
        nombre = traducir(kata.get("name", slug))
        descripcion = traducir(kata.get("description", "Sin descripción"))

        if len(descripcion) > 4093:
            descripcion = descripcion[:4093] + "..."

        embed = discord.Embed(
            title=nombre,
            url=f"https://www.codewars.com/kata/{slug}",
            description=descripcion,
            color=COLORES.get(key, discord.Color.orange())
        )
        embed.add_field(name="Dificultad", value=kata.get("rank", {}).get("name", key), inline=True)
        embed.add_field(name="Tags", value=" • ".join(kata.get("tags", [])) or "N/A", inline=True)
        embed.add_field(name="Link", value=f"https://www.codewars.com/kata/{slug}", inline=False)
        embed.set_footer(text=f"Pedido por {ctx.author.display_name} • {datetime.now().strftime('%d/%m/%Y')}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Daily(bot))