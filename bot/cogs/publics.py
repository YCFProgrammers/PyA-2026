import discord
from discord.ext import commands

import discord
import aiohttp
import random
import json
from datetime import datetime
from discord.ext import commands

# ==============================
# 📚 METADATA DE COMANDOS
# ==============================
COMMANDS_META = {
    "python": {
        "description": "Documentación de librerías estándar de Python",
        "usage": "-python <libreria>",
        "category": "Docs"
    },
    "ml": {
        "description": "Documentación de Machine Learning",
        "usage": "-ml <libreria>",
        "category": "Docs"
    },
    "api": {
        "description": "Documentación de APIs y backend",
        "usage": "-api <libreria>",
        "category": "Docs"
    },
    "exercise": {
        "description": "Devuelve un ejercicio de Codewars",
        "usage": "-exercise <1-8>",
        "category": "Codewars"
    },
    "help": {
        "description": "Muestra todos los comandos",
        "usage": "-help",
        "category": "General"
    },
    "anuncio": {
        "description": "Envía un anuncio a todos",
        "usage": "-anuncio <titulo> <mensaje>",
        "category": "Moderation"
    },
    "kick": {
        "description": "Expulsa a un usuario",
        "usage": "-kick <usuario> [razón]",
        "category": "Moderation"
    },
    "ban": {
        "description": "Banea a un usuario permanentemente",
        "usage": "-ban <usuario> confirm:SI [razón]",
        "category": "Moderation"
    },
    "mute": {
        "description": "Silencia a un usuario por tiempo determinado",
        "usage": "-mute <usuario> <unidad> <cantidad> [razón]",
        "category": "Moderation"
    },
    "warn": {
        "description": "Da una advertencia a un usuario",
        "usage": "-warn <usuario> [razón]",
        "category": "Moderation"
    },
    "warnings": {
        "description": "Lista warnings de un usuario",
        "usage": "-warnings <usuario>",
        "category": "Moderation"
    },
    "clearwarns": {
        "description": "Borra todos los warnings de un usuario",
        "usage": "-clearwarns <usuario>",
        "category": "Moderation"
    }
}



# ---- DICCIONARIO ----
DOCS = {
    "python": {
        "python":       ("Python 3",           "https://docs.python.org/3/"),
        "builtins":     ("Built-in Functions", "https://docs.python.org/3/library/functions.html"),
        "string":       ("string",             "https://docs.python.org/3/library/string.html"),
        "list":         ("list",               "https://docs.python.org/3/tutorial/datastructures.html"),
        "dict":         ("dict",               "https://docs.python.org/3/library/stdtypes.html#dict"),
        "os":           ("os",                 "https://docs.python.org/3/library/os.html"),
        "sys":          ("sys",                "https://docs.python.org/3/library/sys.html"),
        "math":         ("math",               "https://docs.python.org/3/library/math.html"),
        "json":         ("json",               "https://docs.python.org/3/library/json.html"),
        "datetime":     ("datetime",           "https://docs.python.org/3/library/datetime.html"),
        "re":           ("re",                 "https://docs.python.org/3/library/re.html"),
        "pathlib":      ("pathlib",            "https://docs.python.org/3/library/pathlib.html"),
        "asyncio":      ("asyncio",            "https://docs.python.org/3/library/asyncio.html"),
        "typing":       ("typing",             "https://docs.python.org/3/library/typing.html"),
        "dataclasses":  ("dataclasses",        "https://docs.python.org/3/library/dataclasses.html"),
        "collections":  ("collections",        "https://docs.python.org/3/library/collections.html"),
        "itertools":    ("itertools",          "https://docs.python.org/3/library/itertools.html"),
        "functools":    ("functools",          "https://docs.python.org/3/library/functools.html"),
        "logging":      ("logging",            "https://docs.python.org/3/library/logging.html"),
        "unittest":     ("unittest",           "https://docs.python.org/3/library/unittest.html"),
        "sqlite3":      ("sqlite3",            "https://docs.python.org/3/library/sqlite3.html"),
        "csv":          ("csv",                "https://docs.python.org/3/library/csv.html"),
        "subprocess":   ("subprocess",         "https://docs.python.org/3/library/subprocess.html"),
        "threading":    ("threading",          "https://docs.python.org/3/library/threading.html"),
        "socket":       ("socket",             "https://docs.python.org/3/library/socket.html"),
        "venv":         ("venv",               "https://docs.python.org/3/library/venv.html"),
        "enum":         ("enum",               "https://docs.python.org/3/library/enum.html"),
        "abc":          ("abc",                "https://docs.python.org/3/library/abc.html"),
    },
    "ml": {
        "numpy":        ("NumPy",              "https://numpy.org/doc/stable/"),
        "pandas":       ("Pandas",             "https://pandas.pydata.org/docs/"),
        "matplotlib":   ("Matplotlib",         "https://matplotlib.org/stable/contents.html"),
        "scikit":       ("Scikit-learn",       "https://scikit-learn.org/stable/"),
        "pytorch":      ("PyTorch",            "https://pytorch.org/docs/stable/"),
        "tensorflow":   ("TensorFlow",         "https://www.tensorflow.org/api_docs/python/"),
        "keras":        ("Keras",              "https://keras.io/api/"),
        "transformers": ("Transformers",       "https://huggingface.co/docs/transformers/"),
        "scipy":        ("SciPy",              "https://docs.scipy.org/doc/scipy/"),
        "plotly":       ("Plotly",             "https://plotly.com/python/"),
    },
    "api": {
        "fastapi":      ("FastAPI",            "https://fastapi.tiangolo.com/"),
        "flask":        ("Flask",              "https://flask.palletsprojects.com/"),
        "django":       ("Django",             "https://docs.djangoproject.com/"),
        "djangorest":   ("Django REST",        "https://www.django-rest-framework.org/"),
        "requests":     ("Requests",           "https://requests.readthedocs.io/"),
        "pydantic":     ("Pydantic",           "https://docs.pydantic.dev/"),
        "sqlalchemy":   ("SQLAlchemy",         "https://docs.sqlalchemy.org/"),
        "pymongo":      ("PyMongo",            "https://pymongo.readthedocs.io/"),
        "redis":        ("Redis-py",           "https://redis-py.readthedocs.io/"),
        "celery":       ("Celery",             "https://docs.celeryq.dev/"),
        "uvicorn":      ("Uvicorn",            "https://www.uvicorn.org/"),
        "jwt":          ("PyJWT",              "https://pyjwt.readthedocs.io/"),
        "dotenv":       ("python-dotenv",      "https://saurabh-kumar.com/python-dotenv/"),
        "json":         ("Json",               "https://docs.python.org/3/library/json.html"),
    },
}

# ---- HELPER ----
def _build_embed(ctx, categoria: str, libreria: str | None):
    catalogo = DOCS[categoria]

    if libreria is None:
        titles = {
            "python": "Documentación — Python Estándar",
            "ml":     "Documentación — Machine Learning",
            "api":    "Documentación — Backend & APIs",
        }
        embed = discord.Embed(title=titles[categoria], color=discord.Color.blue())
        keys_display = " • ".join(f"`{k}`" for k in catalogo)
        embed.add_field(name="Librerías disponibles", value=keys_display, inline=False)
        embed.set_footer(text=f"Uso: /{categoria} <libreria>")
        return embed

    key = libreria.lower()
    resultado = catalogo.get(key)

    if resultado:
        nombre, url = resultado
        embed = discord.Embed(title=nombre, url=url, color=discord.Color.green())
        embed.add_field(name="Link", value=url, inline=False)
        embed.set_footer(text=f"Pedido por {ctx.author.display_name}")
        return embed

    sugerencias = [k for k in catalogo if key in k or k in key]
    embed = discord.Embed(
        title="No encontrado",
        description=f"No hay docs para `{libreria}` en esta categoría.",
        color=discord.Color.red()
    )
    if sugerencias:
        embed.add_field(name="Quizá quisiste decir:", value=" • ".join(f"`{s}`" for s in sugerencias[:5]), inline=False)
    return embed


def build_help_embed(ctx):
    embed = discord.Embed(
        title="📖 Ayuda del Bot",
        color=discord.Color.blurple()
    )

    categorias = {}
    for cmd, info in COMMANDS_META.items():
        categorias.setdefault(info["category"], []).append((cmd, info))

    for cat, comandos in categorias.items():
        texto = ""
        for cmd, info in comandos:
            texto += f"**-{cmd}** → {info['description']}\n"
            texto += f"`{info['usage']}`\n\n"

        embed.add_field(name=f"📂 {cat}", value=texto, inline=False)

    embed.set_footer(text=f"Pedido por {ctx.author.display_name}")
    return embed

# ---- COG ----
class Publics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="python", description="Documentación de Python")
    async def python(self, ctx: commands.Context, libreria: str):
        await ctx.send(embed=_build_embed(ctx, "python", libreria))

    @commands.hybrid_command(name="ml", description="Documentación de Machine Learning")
    async def ml(self, ctx: commands.Context, libreria: str ):
        await ctx.send(embed=_build_embed(ctx, "ml", libreria))

    @commands.hybrid_command(name="api", description="Documentación de APIs y backend")
    async def api(self, ctx: commands.Context, libreria: str):
        await ctx.send(embed=_build_embed(ctx, "api", libreria))
    
    @commands.hybrid_command(name="help", description="Muestra todos los comandos")
    async def help_cmd(self, ctx):
        embed = discord.Embed(
            title="📖 Ayuda del Bot",
            description="Lista de comandos disponibles",
            color=discord.Color.blurple()
        )

        categorias = {}

        # Agrupar por categoría
        for cmd, info in COMMANDS_META.items():
            categorias.setdefault(info["category"], []).append((cmd, info))

        # Construir embed
        for cat, comandos in categorias.items():
            texto = ""
            for cmd, info in comandos:
                texto += f"**-{cmd}**\n"
                texto += f"└ {info['description']}\n"
                texto += f"└ Uso: `{info['usage']}`\n\n"

            embed.add_field(
                name=f"📂 {cat}",
                value=texto,
                inline=False
            )

        embed.set_footer(text=f"Pedido por {ctx.author.display_name}")

        await ctx.send(embed=embed)



async def setup(bot: commands.Bot):
    await bot.add_cog(Publics(bot))