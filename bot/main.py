import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive  # <--- IMPORTANTE: Importar el truco

# 1. Cargar variables
load_dotenv('token.env')
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(
    command_prefix='-',
    intents=discord.Intents.all(),
    help_command=None
)

@bot.event
async def on_ready():
    if not hasattr(bot, '_synced'):
        bot._synced = True
        print(f'✅ Logged in as {bot.user}')
        try:
            # Sync para desarrollo
            guild = discord.Object(id=1490702264917033141)
            synced = await bot.tree.sync(guild=guild)
            print(f'✅ {len(synced)} comando(s) sincronizados')
        except Exception as e:
            print(f'❌ Error sync: {e}')

@bot.event
async def on_command_error(ctx, error):
    # (Mantenemos tu lógica de errores igual...)
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Ese comando no existe.")
    else:
        print(f"Error: {error}")

async def load_cogs():
    cogs = ['cogs.publics', 'cogs.daily', 'cogs.moderation']
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog {cog} cargado")
        except Exception as e:
            print(f"❌ Error cargando {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        # --- EL TRUCO PARA RENDER ---
        print("🌐 Iniciando servidor Keep-Alive...")
        keep_alive() 
        # ----------------------------
        print("🚀 Iniciando el bot...")
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot detenido.")
    except Exception as e:
        print(f"❌ Error crítico: {e}")