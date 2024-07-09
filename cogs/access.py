import discord
import os
import MySQLdb
from discord import app_commands
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_host = os.getenv('DB_HOST')
        self.db_port = int(os.getenv('DB_PORT'))
        self.db_db = os.getenv('VGI_DB')

    group = app_commands.Group(name="access", description="Grants access to the VGI server")

    @group.command(name="invite", description="Generate a temporary invite link")
    async def create_invite_link(self, ctx: discord.Interaction) -> None:
        mod_channel = int(os.getenv("MOD_CHANNEL"))
        invite_code = await ctx.guild.rules_channel.create_invite(max_age=1800, max_uses=1, temporary=True, unique=True)

        mod_alert = discord.Embed(title="Single Use Token Generated", description=f"{ctx.user.nick} ({ctx.user.name}) generated access token: `{invite_code.code}`")
        user_message = discord.Embed(title="Single Use Token Generated", description=f"The following link can be used once, and will last for half an hour.\r\n{invite_code}")
        await self.bot.get_channel(mod_channel).send(embed=mod_alert)
        await ctx.response.send_message(embed=user_message, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        if guild is not None and guild.id == int(os.getenv("GUILD_ID")):
            cnx = MySQLdb.connect(user=self.db_user, password=self.db_password, host=self.db_host, port=self.db_port, database=self.db_db)
            cursor = cnx.cursor()
            cursor.execute("INSERT INTO members (member_id, friendly_name) VALUES (%s, %s)", (member.id, member.name))

            cnx.commit()
            cnx.close()
