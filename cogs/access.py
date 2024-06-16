import discord, os
from discord import app_commands, Member, VoiceState
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        guild_id = int(os.getenv("GUILD_ID"))
        mod_channel = int(os.getenv("MOD_CHANNEL"))
        server = self.bot.get_guild(guild_id)
        default_role_id = server.default_role.id

        if after.channel is not None or before.channel.guild.id != guild_id:
            return

        if len(member.roles) == 1 and member.roles[0].id == default_role_id:
            await member.kick(reason="Purge Temporary User")
            mod_alert = discord.Embed(title="Temporary Access Expired", description=f"{member.nick} ({member.name}) kicked")
            await server.get_channel(mod_channel).send(embed=mod_alert)
