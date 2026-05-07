import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from keep_alive import keep_alive  # <--- IMPORTANTE: Importar el truco

# 1. Cargar variables (path absoluto, funciona desde cualquier CWD)
ENV_PATH = Path(__file__).resolve().parent / "token.env"
load_dotenv(ENV_PATH)
TOKEN = os.getenv('DISCORD_TOKEN')
DEV_GUILD_ID = os.getenv('DEV_GUILD_ID')  # opcional: sync rápido en guild de pruebas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("bot")

# Intents mínimos necesarios (Intents.all() requiere privileged y es caro)
# - guilds: eventos de servidor
# - members: para anti-raid join detection y kick/ban
# - message_content: para leer contenido y moderar
# - messages: eventos de mensaje
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='-',
    intents=intents,
    help_command=None
)


async def load_cogs():
    cogs = ['cogs.publics', 'cogs.daily', 'cogs.moderation', 'cogs.consults_ia']
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            log.info("Cog %s cargado", cog)
        except Exception as e:
            log.error("Error cargando %s: %s", cog, e)


async def _setup_hook():
    # setup_hook corre una sola vez antes del primer on_ready,
    # ideal para cargar cogs y sincronizar comandos
    await load_cogs()
    try:
        if DEV_GUILD_ID:
            # Sync para desarrollo (instantáneo)
            guild = discord.Object(id=int(DEV_GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            log.info("%d comando(s) sincronizados en guild %s", len(synced), DEV_GUILD_ID)
        else:
            synced = await bot.tree.sync()
            log.info("%d comando(s) sincronizados globalmente", len(synced))
    except Exception as e:
        log.error("Error sync: %s", e)


bot.setup_hook = _setup_hook


@bot.event
async def on_ready():
    log.info("Logged in as %s (id=%s)", bot.user, bot.user.id if bot.user else "?")


@bot.event
async def on_command_error(ctx, error):
    # (Mantenemos tu lógica de errores igual...)
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Ese comando no existe.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos para ese comando.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏱️ Espera {error.retry_after:.1f}s antes de reintentar.")
    else:
        log.error("command error: %s", error, exc_info=True)


async def main():
    if not TOKEN:
        raise RuntimeError(f"DISCORD_TOKEN no definido en {ENV_PATH}")

    async with bot:
        # --- EL TRUCO PARA RENDER ---
        log.info("Iniciando servidor Keep-Alive...")
        keep_alive()
        # ----------------------------
        log.info("Iniciando el bot...")
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot detenido.")
    except Exception as e:
        log.critical("Error crítico: %s", e, exc_info=True)
