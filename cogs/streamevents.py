import datetime
import discord
import os
import MySQLdb
from discord import Color, DiscordServerError
from discord.ext import commands, tasks
from twitchAPI.object.api import Stream
from twitchAPI.twitch import Twitch


class StreamEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.socials_check.start()
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_host = os.getenv('DB_HOST')
        self.db_port = int(os.getenv('DB_PORT'))
        self.db_db = os.getenv('VGI_DB')
        self.guild_id = int(os.getenv('GUILD_ID'))
        self.alert_channel = int(os.getenv('ALERT_CHANNEL'))
        self.live_role = int(os.getenv('LIVE_ROLE'))
        self.twitch_client_id = os.getenv('TWITCH_CLIENT_ID')
        self.twitch_client_select = os.getenv('TWITCH_CLIENT_SECRET')
        self.social_records = []

        cnx = MySQLdb.connect(user=self.db_user, password=self.db_password, host=self.db_host, port=self.db_port, database=self.db_db)
        cursor = cnx.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT socials.member_id, socials.social_type, socials.link FROM socials WHERE social_type IN (1,3)')
        for row in cursor.fetchall():
            self.social_records.append({
                'member_id': row['member_id'],
                'social_type': row['social_type'],
                'link': row['link'],
                'last_twitch': datetime.date.today()
            })
        cnx.close()


    @tasks.loop(minutes=1)
    async def socials_check(self):
        if not self.bot.is_ready():
            return

        await self.check_twitch()

    async def check_twitch(self):
        twitch = await Twitch(self.twitch_client_id, self.twitch_client_select)

        twitch_channels = list(filter(lambda x: x['social_type'] == 1, self.social_records))
        twitch_usernames = list(map(lambda x: x['link'], twitch_channels))
        currently_live_channels: [Stream] = []
        guild = self.bot.get_guild(self.guild_id)
        live_role = guild.get_role(self.live_role)

        async for stream in twitch.get_streams(user_login=twitch_usernames):
            currently_live_channels.append(stream)

        try:
            for channel in twitch_channels:
                found_stream = next((x for x in currently_live_channels if x.user_login.lower() == channel["link"].lower()), None)
                discord_member = guild.get_member(channel["member_id"])

                if found_stream is None:
                    if any(role == live_role for role in discord_member.roles):
                        await discord_member.remove_roles(live_role)
                        print(f"removing live role from {discord_member.name}")
                else:
                    stream_start = found_stream.started_at

                    if channel["last_twitch"] == stream_start:
                        continue

                    channel["last_twitch"] = stream_start
                    if not any(role == live_role for role in discord_member.roles):
                        await discord_member.add_roles(live_role)
                        print(f"giving live role to {discord_member.name}")

                    twitch_notification = discord.Embed(title=f'{found_stream.user_name} is now LIVE with {found_stream.game_name}!!',
                                                        description=f'{found_stream.title}',
                                                        url=f'https://twitch.tv/{found_stream.user_name}',
                                                        timestamp=stream_start,
                                                        color=Color.from_str('0x6034B2'))
                    twitch_notification.set_image(url=found_stream.thumbnail_url.replace('{width}x{height}', '640x360'))
                    await self.bot.get_channel(self.alert_channel).send(embed=twitch_notification)
        except DiscordServerError:
            print("something went wrong here")
        except Exception as e:
            print(e)
