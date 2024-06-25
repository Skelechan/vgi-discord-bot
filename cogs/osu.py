import discord, os, time, mysql.connector
from dotenv import load_dotenv
from discord import app_commands, Color
from discord.ext import commands


class Osu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.color = Color.from_str('0xA65973')

    load_dotenv()
    admin_role = int(os.getenv("ADMIN_ROLE"))
    osu_group = app_commands.Group(name="osu", description="Commands related to the VGI Osu! server")

    @osu_group.command(name="stats", description="Get a user profile")
    @app_commands.describe(user="The stats you want to load")
    async def get_profile(self, ctx: discord.Interaction, user: discord.Member) -> None:
        with mysql.connector.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('OSU_DB')) as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT user_id, user_name, user_country, stats_mode, stats_tscore, stats_rscore, stats_pp, stats_plays, stats_playtime, stats_acc, stats_max_combo, stats_xh_count, stats_x_count, stats_sh_count, stats_s_count, stats_a_count, stats_ranking "
                                        "FROM bancho.v_leaderboard "
                                        "WHERE user_discord_id = %s "
                                        "AND stats_mode = 0 "
                                        "ORDER BY stats_pp DESC", params=[user.id])
                row = cursor.fetchone()
                user_id = row["user_id"]
                osu_url = os.getenv('OSU_URL')

                profile_message = discord.Embed(color=self.color,
                                                description=f"• **Leaderboard Rank:** #{row['stats_ranking']}\r\n"
                                                            f"• **PP:** {row['stats_pp']}pp\r\n"
                                                            f"• **Accuracy:** {round(row['stats_acc'], 2)}%\r\n"
                                                            f"• **Playcount:** {row['stats_plays']} ({row['stats_playtime'] / 3600} hours)\r\n"
                                                            f"• **Max Combo:** x{row['stats_max_combo']}\r\n"
                                                            f"{self.map_grade('SS')} `{row['stats_xh_count']}`\t"
                                                            f"{self.map_grade('SSH')} `{row['stats_x_count']}`\t"
                                                            f"{self.map_grade('S')} `{row['stats_sh_count']}`\t"
                                                            f"{self.map_grade('SH')} `{row['stats_s_count']}`\t"
                                                            f"{self.map_grade('A')} `{row['stats_a_count']}`")
                profile_message.set_author(name=f'Osu! profile for {user.nick}',
                                           icon_url=f'https://{osu_url}/static/images/flags/{row["user_country"].upper()}.png',
                                           url=f'https://{osu_url}/u/{user_id}')
                profile_message.set_thumbnail(url=f'https://a.{osu_url}/{user_id}')
                await ctx.response.send_message(embed=profile_message)

    @osu_group.command(name="top", description="Get top plays")
    @app_commands.describe(user="Filter top plays by user")
    async def get_top(self, ctx: discord.Interaction, user: discord.Member | None) -> None:
        with mysql.connector.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('OSU_DB')) as connection:
            with connection.cursor(dictionary=True) as cursor:
                sql = ("SELECT user_id, user_name,user_country, map_set_id, map_id, map_version, map_title, map_max_combo, map_diff, mod_name, score_mode, score_score, score_grade, score_pp, score_acc, score_max_combo, score_n300, score_n100, score_n50, score_nmiss, score_play_time "
                       "FROM bancho.v_scores "
                       "WHERE score_mode = 0 "
                       "AND score_grade != 'F'")

                if user is not None:
                    sql += ("AND user_discord_id = %s "
                            "ORDER BY score_pp DESC LIMIT 5")
                    cursor.execute(sql, params=[user.id])
                else:
                    sql += "ORDER BY score_pp DESC LIMIT 5"
                    cursor.execute(sql)

                rows = cursor.fetchall()

                primary_id: None | str = None
                primary_location: None | str = None
                description: str = ''
                osu_url = os.getenv('OSU_URL')
                index = 1

                for row in rows:
                    if primary_id is None:
                        primary_id = row['user_id']
                        primary_location = row['user_country']

                    score_date = int(time.mktime(row['score_play_time'].timetuple()))
                    description += (f"**{index}.** [**{row['map_title']} [{row['map_version']}]**](https://osu.ppy.sh/beatmapsets/{row['map_set_id']}#{row['score_mode']}/{row['map_id']}) **{row['mod_name']}** [\u2605 {round(row['map_diff'], 2)}]\r\n"
                                    f"• {self.map_grade(row['score_grade'])} • {round(row['score_pp'], 0)}PP • {round(row['score_acc'], 2)}%\r\n"
                                    f"• {round(row['score_score'], 0)} • x{round(row['score_max_combo'], 0)}/{round(row['map_max_combo'], 0)} • [{round(row['score_n300'], 0)}/{round(row['score_n100'], 0)}/{round(row['score_n50'], 0)}/{round(row['score_nmiss'], 0)}]\r\n"
                                    f"• <t:{score_date}:R> by {row['user_name']}\r\n"
                                    "\r\n")
                    index = index + 1

                stats_message = discord.Embed(color=self.color, description=description)
                if user is not None:
                    stats_message.set_author(name=f'Top 5 Osu! Scores for {user.nick}',
                                             icon_url=f'https://{osu_url}/static/images/flags/{primary_location.upper()}.png',
                                             url=f'https://{osu_url}/u/{primary_id}')
                else:
                    stats_message.set_author(name=f'Top 5 Osu! Scores', icon_url=f'https://{osu_url}/static/images/flags/{primary_location.upper()}.png')

                stats_message.set_thumbnail(url=f'https://a.{osu_url}/{primary_id}')
                await ctx.response.send_message(embed=stats_message)

    @osu_group.command(name="recent", description="Get most recent plays")
    @app_commands.describe(user="Filter recent plays by user")
    async def get_recent(self, ctx: discord.Interaction, user: discord.Member | None) -> None:
        with mysql.connector.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('OSU_DB')) as connection:
            with connection.cursor(dictionary=True) as cursor:
                sql = ("SELECT user_id, user_name,user_country, map_set_id, map_id, map_version, map_title, map_max_combo, map_diff, mod_name, score_mode, score_score, score_grade, score_pp, score_acc, score_max_combo, score_n300, score_n100, score_n50, score_nmiss, score_play_time "
                       "FROM bancho.v_scores "
                       "WHERE score_mode = 0 ")

                if user is not None:
                    sql += ("AND user_discord_id = %s "
                            "LIMIT 5")
                    cursor.execute(sql, params=[user.id])
                else:
                    sql += "LIMIT 5"
                    cursor.execute(sql)

                rows = cursor.fetchall()

                primary_id: None | str = None
                primary_location: None | str = None
                description: str = ''
                osu_url = os.getenv('OSU_URL')
                index = 1

                for row in rows:
                    if primary_id is None:
                        primary_id = row['user_id']
                        primary_location = row['user_country']

                    score_date = int(time.mktime(row['score_play_time'].timetuple()))
                    description += (f"**{index}.** [**{row['map_title']} [{row['map_version']}]**](https://osu.ppy.sh/beatmapsets/{row['map_set_id']}#{row['score_mode']}/{row['map_id']}) **{row['mod_name']}** [\u2605 {round(row['map_diff'], 2)}]\r\n"
                                    f"• {self.map_grade(row['score_grade'])} • {round(row['score_pp'], 0)}PP • {round(row['score_acc'], 2)}%\r\n"
                                    f"• {round(row['score_score'], 0)} • x{round(row['score_max_combo'], 0)}/{round(row['map_max_combo'], 0)} • [{round(row['score_n300'], 0)}/{round(row['score_n100'], 0)}/{round(row['score_n50'], 0)}/{round(row['score_nmiss'], 0)}]\r\n"
                                    f"• <t:{score_date}:R> by {row['user_name']}\r\n"
                                    "\r\n")
                    index = index + 1

                stats_message = discord.Embed(color=self.color, description=description)
                if user is not None:
                    stats_message.set_author(name=f'Recent Osu! Scores for {user.nick}',
                                             icon_url=f'https://{osu_url}/static/images/flags/{primary_location.upper()}.png',
                                             url=f'https://{osu_url}/u/{primary_id}')
                else:
                    stats_message.set_author(name=f'Recent Osu! Scores', icon_url=f'https://{osu_url}/static/images/flags/{primary_location.upper()}.png')

                stats_message.set_thumbnail(url=f'https://a.{osu_url}/{primary_id}')
                await ctx.response.send_message(embed=stats_message)

    @osu_group.command(name="leaderboard", description="Get Osu! leaderboard")
    async def get_leaderboard(self, ctx: discord.Interaction) -> None:
        with mysql.connector.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('OSU_DB')) as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(("SELECT user_id, user_name, user_country, stats_pp, stats_acc, stats_max_combo "
                                "FROM bancho.v_leaderboard "
                                "WHERE stats_mode = 0 "))
                rows = cursor.fetchall()

                primary_id: None | str = None
                primary_location: None | str = None
                description: str = ''
                osu_url = os.getenv('OSU_URL')
                index = 1

                for row in rows:
                    if primary_id is None:
                        primary_id = row['user_id']
                        primary_location = row['user_country']

                    user_name = row['user_name']
                    stats_pp = row['stats_pp']
                    stats_acc = row['stats_acc']
                    stats_max_combo = row['stats_max_combo']

                    description += (f"**{index}.** **{user_name}**\r\n"
                                    f"• {round(stats_pp,0)}PP • {round(stats_acc,2)}% • x{stats_max_combo}\r\n"
                                    "\r\n")
                    index = index + 1

                leaderboard_message = discord.Embed(color=self.color, description=description)
                leaderboard_message.set_author(name=f'Osu! Leaderboard', icon_url=f'https://{osu_url}/static/images/flags/{primary_location.upper()}.png', url=f"https://{osu_url}/leaderboard/std/rscore/vn")
                leaderboard_message.set_thumbnail(url=f'https://a.{osu_url}/{primary_id}')
                await ctx.response.send_message(embed=leaderboard_message)

    @osu_group.command(name="code", description="Get secret join code")
    async def get_leaderboard(self, ctx: discord.Interaction) -> None:
        leaderboard_message = discord.Embed(color=self.color, description=os.getenv("OSU_SECRET_CODE"))
        await ctx.response.send_message(embed=leaderboard_message)

    @staticmethod
    def map_grade(grade: str) -> str:
        match grade:
            case 'A':
                return os.getenv('OSU_A_RANK_EMOJI')
            case 'B':
                return os.getenv('OSU_B_RANK_EMOJI')
            case 'C':
                return os.getenv('OSU_C_RANK_EMOJI')
            case 'D':
                return os.getenv('OSU_D_RANK_EMOJI')
            case 'F':
                return os.getenv('OSU_F_RANK_EMOJI')
            case 'S':
                return os.getenv('OSU_S_RANK_EMOJI')
            case 'SH':
                return os.getenv('OSU_SPlus_RANK_EMOJI')
            case 'SS':
                return os.getenv('OSU_SS_RANK_EMOJI')
            case 'SSH':
                return os.getenv('OSU_SSPlus_RANK_EMOJI')

