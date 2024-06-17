import os, mysql.connector, discord
from discord import Color
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch


class StreamEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.twitch_check.start()
        self.last_stream = {}

    @tasks.loop(minutes=1)
    async def twitch_check(self):
        if not self.bot.is_ready():
            return
        twitch_channels: [str] = []

        cnx = mysql.connector.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('VGI_DB'))
        if cnx and cnx.is_connected():
            with cnx.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT link FROM socials WHERE social_type = 1')
                for row in cursor.fetchall():
                    twitch_channels.append(row['link'])

            twitch = await Twitch(os.getenv('TWITCH_CLIENT_ID'), os.getenv('TWITCH_CLIENT_SECRET'))

            async for stream in twitch.get_streams(user_login=twitch_channels):
                login = stream.user_login

                if login in self.last_stream:
                    if self.last_stream[login] == stream.started_at:
                        continue

                self.last_stream[login] = stream.started_at

                twitch_notification = discord.Embed(title=f'{stream.user_name} is now LIVE with {stream.game_name}!!',
                                                    description=f'{stream.title}',
                                                    url=f'https://twitch.tv/{stream.user_name}',
                                                    timestamp=stream.started_at,
                                                    color=Color.from_str('0x6034B2'))
                twitch_notification.set_image(url=stream.thumbnail_url.replace('{width}x{height}', '640x360'))

                await self.bot.get_channel(int(os.getenv('ALERT_CHANNEL'))).send(embed=twitch_notification)
