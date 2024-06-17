import discord, os
from dotenv import load_dotenv
from discord.ext import commands
from cogs.access import Admin
from cogs.birthday import Birthday
from cogs.general import General
from cogs.osu import Osu
from cogs.streamevents import StreamEvents
from cogs.twitter import Twitter

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)


@bot.event
async def on_ready():
    await bot.add_cog(Admin(bot))
    await bot.add_cog(Twitter(bot))
    await bot.add_cog(Osu(bot))
    await bot.add_cog(Birthday(bot))
    await bot.add_cog(General(bot))
    await bot.add_cog(StreamEvents(bot))
    await bot.tree.sync()
    print('Ready!')

bot.run(os.getenv('DISCORD_KEY'))
