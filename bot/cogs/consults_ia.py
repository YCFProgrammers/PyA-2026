import discord

from discord.ext import commands

class Consults(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    

async def setup(bot):
    await bot.add_cog(Consults(bot))