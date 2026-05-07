import asyncio
import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp
import discord
from deep_translator import GoogleTranslator
from discord.ext import commands

log = logging.getLogger(__name__)

# ---- Llamar al exercise.json ----
# fix: path absoluto para que funcione desde cualquier CWD
KATAS_PATH = Path(__file__).resolve().parent.parent / "exercises.json"
TRANSLATION_CACHE_PATH = Path(__file__).resolve().parent.parent / ".translation_cache.json"

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

CODE_BLOCK_RE = re.compile(r"(```[\s\S]*?```|`[^`\n]+`)")
NON_PYTHON_BLOCK_RE = re.compile(r"```(?!python\b)\w+[\s\S]*?```")
TILDE_RE = re.compile(r"~~+")


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log.warning("json corrupto en %s: %s", path, e)
        return {}


def _save_json(path: Path, data: dict) -> None:
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError as e:
        log.warning("no se pudo escribir %s: %s", path, e)


# ---- Helper de traducción ----


def _traducir_sync(texto: str) -> str:
    try:
        # Eliminar bloques de lenguajes específicos irrelevantes
        texto = NON_PYTHON_BLOCK_RE.sub("", texto)

        # Limpiar tildes sueltas que quedan (evita tachado en Discord)
        texto = TILDE_RE.sub("", texto)

        # Separar bloques de código restantes del texto normal
        partes = CODE_BLOCK_RE.split(texto)
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
    except Exception as e:
        log.warning("translation failed: %s", e)
        return texto


# ---- Helper ----
async def _fetch_kata(session: aiohttp.ClientSession, slug: str) -> Optional[dict]:
    url = f"https://www.codewars.com/api/v1/code-challenges/{slug}"
    try:
        async with session.get(url) as response:
            log.info("codewars %s -> %s", slug, response.status)
            if response.status == 200:
                return await response.json()
            return None
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        log.warning("codewars fetch error %s: %s", slug, e)
        return None


# ---- Clase ----
class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.katas: dict[str, list[str]] = {}
        self._translation_cache: dict[str, str] = {}

    async def cog_load(self) -> None:
        # Cargar JSONs en cog_load para no romper el import si faltan archivos
        self.katas = _load_json(KATAS_PATH)
        if not self.katas:
            log.warning("exercises.json vacío o inexistente en %s", KATAS_PATH)
        self._translation_cache = _load_json(TRANSLATION_CACHE_PATH)

    async def _traducir(self, texto: str, cache_key: Optional[str] = None) -> str:
        # cache por slug+campo para evitar reconsultar Google Translate
        if cache_key and cache_key in self._translation_cache:
            return self._translation_cache[cache_key]
        # GoogleTranslator es bloqueante, mover a thread para no congelar el loop
        traducido = await asyncio.to_thread(_traducir_sync, texto)
        if cache_key:
            self._translation_cache[cache_key] = traducido
            _save_json(TRANSLATION_CACHE_PATH, self._translation_cache)
        return traducido

    @commands.hybrid_command(name="exercise", description="Devuelve un ejercicio de dificultad dada del 1(dificil) al 8(facil), de la pagina codewars")
    async def exercise(self, ctx: commands.Context, difficulty: Optional[int] = None):
        # Si no pasan difficulty, listar opciones disponibles
        if difficulty is None:
            embed = discord.Embed(
                title="Ejercicio diario — Codewars",
                description="Elige una dificultad:",
                color=discord.Color.orange()
            )
            for level, katas in sorted(self.katas.items()):
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
        if key not in self.katas or not self.katas[key]:
            embed = discord.Embed(
                title="Dificultad no valida",
                description=f"`{difficulty}` no existe o no tiene katas.",
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

        # Seleccionar kata aleatorio y llamar a la API con retry
        timeout = aiohttp.ClientTimeout(total=10)
        kata = None
        slug = None
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for _ in range(3):
                slug = random.choice(self.katas[key])
                kata = await _fetch_kata(session, slug)
                if kata:
                    break

        if kata is None or slug is None:
            await ctx.send("No se pudo obtener el kata, intenta de nuevo.")
            return

        # Traducir nombre y descripción (con cache por slug)
        nombre = await self._traducir(kata.get("name", slug), cache_key=f"{slug}:name")
        descripcion = await self._traducir(kata.get("description", "Sin descripción"), cache_key=f"{slug}:desc")

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
