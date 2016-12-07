import discord
from discord.ext import commands
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO
import asyncio
from random import choice as randchoice
from .utils import checks
import tweepy

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class Twitter:
    """Cog to get twitter feeds"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/twitter/settings.json"
        self.settings = dataIO.load_json(self.file_path)
        self.feeds_file_path = "data/twitter/feeds.json"
        self.feeds = dataIO.load_json(self.feeds_file_path)

    def authenticate(self):
        auth = tweepy.OAuthHandler(self.settings["CONSUMER_KEY"], self.settings["CONSUMER_SECRET"])
        auth.set_access_token(self.settings["ACCESS_TOKEN"], self.settings["ACCESS_TOKEN_SECRET"])
        self.twitterAPI = tweepy.API(auth)

    @commands.group(pass_context=True, no_pm=True, name="twitter", aliases=["tw"])
    async def _twitter(self, context):
        """Posts new tweets in discord"""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_twitter.command(no_pm=True, name="add")
    @checks.serverowner_or_permissions(administrator=True)
    async def _add(self, username : str, channel : discord.Channel):
        """Adds a new twitter user feed to a channel"""
        self.authenticate()

        try:
            twitterUser = self.twitterAPI.get_user(username)
            twitterUserTimeline = twitterUser.timeline(include_rts=True, count=1)
        except Exception:
            await self.bot.say("Something went wrong!")
            return

        lastId = 0
        if len(twitterUserTimeline) > 0:
            lastId = twitterUserTimeline[0].id

        self.feeds.append({"userName": username,
            "channelId" : channel.id,
            "serverId" : channel.server.id,
            "lastId": lastId})
        dataIO.save_json(self.feeds_file_path, self.feeds)

        await self.bot.say("Added user to database!")

    @_twitter.command(pass_context=True, no_pm=True, name="list")
    @checks.serverowner_or_permissions(administrator=True)
    async def _list(self, ctx):
        """Lists all twitter users in the database on this server"""
        server = ctx.message.server

        listMessage = ""
        for feed in self.feeds:
            if feed["serverId"] == server.id:
                listMessage += "#{1}: `@{0[userName]}` posting to <#{0[channelId]}>\n".format(feed, self.feeds.index(feed))

        if listMessage == "":
            await self.bot.say("No user in database!")
            return

        await self.bot.say("Found these users:\n{0}".format(listMessage))

    @_twitter.command(no_pm=True, name="del")
    @checks.serverowner_or_permissions(administrator=True)
    async def _del(self, feedId : int):
        """Deletes an twitter user from the database"""

        try:
            del(self.feeds[feedId])
        except IndexError:
            await self.bot.say("Entry not found in database!")
            return

        dataIO.save_json(self.feeds_file_path, self.feeds)

        await self.bot.say("User deleted from database")

    @_twitter.command(no_pm=True, name="force", hidden=True)
    @checks.serverowner_or_permissions(administrator=True)
    async def _force(self, username : str, channel : discord.Channel):
        """Forces to print the latest tweet"""
        self.authenticate()

        try:
            twitterUserTimeline = self.twitterAPI.user_timeline(screen_name=username, include_rts=True, count=1)
        except Exception:
            await self.bot.say("Something went wrong!")
            return

        if len(twitterUserTimeline) <= 0:
            await self.bot.say("No tweets found!")
            return

        data = self.get_embed_for_item(twitterUserTimeline[0])
        await self.bot.send_message(channel, embed=data)

    def get_embed_for_item(self, item):
        colour = int("1DA1F2", 16)

        itemUserFullname = item.user.name
        itemUserName = item.user.screen_name
        itemUserProfilepicture = item.user.profile_image_url_https
        itemCaption = item.text
        itemUrl = "https://twitter.com/statuses/{0}".format(item.id_str)

        data = discord.Embed(
            description=itemCaption,
            colour=discord.Colour(value=colour))
        data.set_author(name="{0} (@{1})".format(itemUserFullname, itemUserName), icon_url=itemUserProfilepicture, url=itemUrl)

        if "media" in item.entities and len(item.entities["media"]) > 0:
            data.set_image(url=item.entities["media"][0]["media_url_https"])
        data.set_footer(text="via twitter")
        return data

    async def check_feed_loop(self):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('Twitter'):
            self.authenticate()
            for feed in self.feeds:
                channel = self.bot.get_channel(feed["channelId"])
                if channel == None:
                    print("Channel not found")
                    continue
                try:
                    if feed["lastId"] == 0:
                        twitterUserTimeline = self.twitterAPI.user_timeline(screen_name=feed["userName"], include_rts=True)
                    else:
                        twitterUserTimeline = self.twitterAPI.user_timeline(screen_name=feed["userName"], include_rts=True, since_id=feed["lastId"])
                except Exception:
                    print("something went wrong fetching twitter account")
                    continue

                if len(twitterUserTimeline) > 0:
                    self.feeds[self.feeds.index(feed)]["lastId"] = twitterUserTimeline[0].id
                    dataIO.save_json(self.feeds_file_path, self.feeds)

                for item in twitterUserTimeline:
                    data = self.get_embed_for_item(item)
                    await self.bot.send_message(channel, embed=data)
            await asyncio.sleep(600)

def check_folders():
    folders = ("data", "data/twitter/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"ACCESS_TOKEN": "yourtwitteraccesstoken",
    "ACCESS_TOKEN_SECRET" : "yourtwitteraccesstokensecret",
    "CONSUMER_KEY" : "yourtwitterconsumerkey",
    "CONSUMER_SECRET" : "yourtwitterconsumersecret"
    }
    feeds = []

    if not os.path.isfile("data/twitter/settings.json"):
        print("Creating empty settings.json, please fill in details...")
        dataIO.save_json("data/twitter/settings.json", settings)
    if not os.path.isfile("data/twitter/feeds.json"):
        print("Creating empty feeds.json...")
        dataIO.save_json("data/twitter/feeds.json", feeds)

def setup(bot):
    check_folders()
    check_files()
    n = Twitter(bot)
    bot.add_cog(n)
    bot.loop.create_task(n.check_feed_loop())
