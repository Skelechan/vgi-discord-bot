import os, mysql.connector, discord
from discord import Color
from discord.ext import commands, tasks
from twitchAPI.object.api import Stream
from twitchAPI.twitch import Twitch


class StreamEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.socials_check.start()
        self.last_twitch_stream = {}
        self.guild_id = int(os.getenv('GUILD_ID'))
        self.alert_channel = int(os.getenv('ALERT_CHANNEL'))
        self.live_role = int(os.getenv('LIVE_ROLE'))

    @tasks.loop(minutes=1)
    async def socials_check(self):
        if not self.bot.is_ready():
            return
        social_records = []

        cnx = mysql.connector.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('VGI_DB'))
        if cnx and cnx.is_connected():
            with cnx.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT socials.member_id, socials.social_type, socials.link FROM socials WHERE social_type IN (1,3)')
                for row in cursor.fetchall():
                    social_records.append({
                        'member_id': row['member_id'],
                        'social_type': row['social_type'],
                        'link': row['link'],
                    })

            await self.check_twitch(social_records)

    async def check_twitch(self, social_records):
        twitch = await Twitch(os.getenv('TWITCH_CLIENT_ID'), os.getenv('TWITCH_CLIENT_SECRET'))

        twitch_channels = list(filter(lambda x: x['social_type'] == 1, social_records))
        twitch_usernames = list(map(lambda x: x['link'], twitch_channels))
        currently_live_channels: [Stream] = []
        guild = self.bot.get_guild(self.guild_id)
        live_role = guild.get_role(self.live_role)

        async for stream in twitch.get_streams(user_login=twitch_usernames):
            currently_live_channels.append(stream)

        for member in twitch_channels:
            found_stream = next((x for x in currently_live_channels if x.user_login.lower() == member["link"].lower()), None)
            member = guild.get_member(member["member_id"])

            if found_stream is None:
                await member.remove_roles(live_role)
            else:
                user_login = found_stream.user_login
                stream_start = found_stream.started_at

                if user_login in self.last_twitch_stream and self.last_twitch_stream[user_login] == stream_start:
                    continue

                self.last_twitch_stream[user_login] = stream_start
                await member.add_roles(live_role)
                twitch_notification = discord.Embed(title=f'{found_stream.user_name} is now LIVE with {found_stream.game_name}!!',
                                                description=f'{found_stream.title}',
                                                url=f'https://twitch.tv/{found_stream.user_name}',
                                                timestamp=stream_start,
                                                color=Color.from_str('0x6034B2'))
                twitch_notification.set_image(url=found_stream.thumbnail_url.replace('{width}x{height}', '640x360'))
                await self.bot.get_channel(int(os.getenv('ALERT_CHANNEL'))).send(embed=twitch_notification)