import discord
import os
import re
import tweepy
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from tweepy import Response


class Twitter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    load_dotenv()
    admin_role = int(os.getenv("ADMIN_ROLE"))

    @app_commands.command(name="tweet", description="Publicly post on the VGI Twitter")
    @app_commands.checks.has_role(admin_role)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(content="The message to tweet on main", url="The URL to QRT")
    async def post_tweet(self, ctx: discord.Interaction, content: str, url: str | None) -> None:
        if await self.tweet_fails_validation(ctx, content):
            return

        tweet_id = None
        if url is not None:
            try:
                matches = re.match(r'.*/status/(\d+)', url)
                tweet_id = matches.group(1)
            except:
                error_message = discord.Embed(title="Could not send Retweet",
                                              description="That doesn't look like a valid twitter URL?")
                await ctx.response.send_message(embed=error_message, ephemeral=True)
                return

        client = tweepy.Client(consumer_key=os.getenv("TWITTER_CONSUMER_KEY"), consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"), access_token=os.getenv("TWITTER_TOKEN_KEY"), access_token_secret=os.getenv("TWITTER_TOKEN_SECRET"))
        twitter_response = client.create_tweet(text=content, quote_tweet_id=tweet_id)

        await self.resolve_twitter_response(ctx, content, twitter_response)

    @staticmethod
    async def resolve_twitter_response(ctx: discord.Interaction, content, twitter_response):
        if isinstance(twitter_response, Response):
            success_message = discord.Embed(title="Tweet Sent", description=content, url=f"https://x.com/{os.getenv('TWITTER_ACCOUNT_NAME')}/status/{twitter_response.data['id']}")
            await ctx.response.send_message(embed=success_message, ephemeral=True)
            return

        maybe_message = discord.Embed(title="IDK",description="Twitter responded weirdly, the tweet might be there now?")
        await ctx.response.send_message(embed=maybe_message, ephemeral=True)

    @staticmethod
    async def tweet_fails_validation(ctx: discord.Interaction, content) -> bool:
        if len(content) <= 0:
            error_message = discord.Embed(title="Could not send Tweet", description="Is that even a message?")
            await ctx.response.send_message(embed=error_message, ephemeral=True)
            return True

        if len(content) > 280:
            error_message = discord.Embed(title="Could not send Tweet", description="Message was over 280 characters long")
            await ctx.response.send_message(embed=error_message, ephemeral=True)
            return True
        return False
