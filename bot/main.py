import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

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
            # Solo sync al servidor para desarrollo (instantáneo)
            guild = discord.Object(id=1490702264917033141)
            synced = await bot.tree.sync(guild=guild)
            print(f'✅ {len(synced)} comando(s) sincronizados al servidor')
        except Exception as e:
            print(f'❌ Error durante la sincronización: {e}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Ese comando no existe. Usá `-help` para ver los disponibles.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Te falta un argumento: `{error.param.name}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argumento inválido.")
    else:
        await ctx.send(f"❌ Error inesperado: {error}")
        raise error

async def load_cogs():
    try:
        await bot.load_extension('cogs.publics')
        await bot.load_extension('cogs.daily')
        await bot.load_extension('cogs.moderation')
        print("✅ Todos los cogs cargados correctamente")
    except Exception as e:
        print(f"❌ Error cargando cogs: {e}")

async def main():
    async with bot:
        await load_cogs()
        print("🚀 Iniciando el bot...")
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot detenido manualmente.")
    except Exception as e:
        print(f"❌ Error crítico al iniciar el bot: {e}")