import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="code", description="The source code of this bot")
    async def post_tweet(self, ctx: discord.Interaction) -> None:
        error_message = discord.Embed(title="https://github.com/Skelechan/vgi-discord-bot", description="Written and maintained by skelly", url='https://github.com/Skelechan/vgi-discord-bot')
        await ctx.response.send_message(embed=error_message, ephemeral=True)
