import datetime
import discord
import os
import MySQLdb
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv


class Birthday(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_host = os.getenv('DB_HOST')
        self.db_port = int(os.getenv('DB_PORT'))
        self.db_db = os.getenv('VGI_DB')
        self.birthday_channel = int(os.getenv("BIRTHDAY_CHANNEL"))
        self.last_run: datetime = None
        self.birthday_check.start()

    load_dotenv()
    birthday_group = app_commands.Group(name="birthday", description="Birthday Check")

    @birthday_group.command(name="set", description="Set your birthday")
    @app_commands.describe(day="The day you were born (1 - 31)", month="The month you were born (1 - 12)")
    async def get_profile(self, ctx: discord.Interaction, day: int, month: int) -> None:
        match month:
            case 4 | 6 | 9 | 12:
                if day < 1 or day > 30:
                    error_message = discord.Embed(description="That date doesn't seem right, please set day to between 1 and 30")
                    await ctx.response.send_message(embed=error_message, ephemeral=True)
                    return
            case 1 | 3 | 5 | 7 | 8 | 10 | 12:
                if day < 1 or day > 31:
                    error_message = discord.Embed(description="That date doesn't seem right, please set day to between 1 and 31")
                    await ctx.response.send_message(embed=error_message, ephemeral=True)
                    return
            case 2:
                if day < 1 or day > 28:
                    error_message = discord.Embed(description="That date doesn't seem right, please set day to between 1 and 28")
                    await ctx.response.send_message(embed=error_message, ephemeral=True)
                    return
            case _:
                error_message = discord.Embed(description="That date doesn't seem right, please set months to between 1 and 12")
                await ctx.response.send_message(embed=error_message, ephemeral=True)
                return

        birth_date = datetime.date(day=day, month=month, year=2024)
        cnx = MySQLdb.connect(user=self.db_user, password=self.db_password, host=self.db_host, port=self.db_port, database=self.db_db)
        cursor = cnx.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute('SELECT COUNT(member_id) FROM members WHERE member_id = %s', (ctx.user.id))
        member_count = cursor.fetchone()

        if member_count['COUNT(member_id)'] == 0:
            cursor.execute('INSERT INTO members (member_id, birthday) VALUES (%s, %s)', (ctx.user.id, birth_date))
        else:
            cursor.execute('UPDATE members SET birthday = %s WHERE member_id = %s', (birth_date, ctx.user.id))

        cnx.commit()
        cnx.close()

        error_message = discord.Embed(description=f"YIPPEEEEEEE. Your birthday has been set to {day}/{month}")
        await ctx.response.send_message(embed=error_message, ephemeral=True)


    @tasks.loop(minutes=1)
    async def birthday_check(self):
        if not self.bot.is_ready():
            return

        today = datetime.date.today()
        if self.last_run is None or self.last_run != today:
            self.last_run = today

            cnx = MySQLdb.connect(user=self.db_user, password=self.db_password, host=self.db_host, port=self.db_port, database=self.db_db)
            cursor = cnx.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT member_id FROM members WHERE MONTH(birthday) = %s AND DAY(birthday) = %s', (today.month, today.day))
            rows = cursor.fetchall()

            for row in rows:
                embed = discord.Embed(title="HAPPY BIRTHDAY", description=f"YIPPEEEE. Today is <@{row['member_id']}>'s birthday!!!!")
                await self.bot.get_channel(self.birthday_channel).send(embed=embed)

            cursor.close()
