import discord
from discord.ext import commands
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO
import asyncio
from random import choice as randchoice
from .utils import checks
import tweepy
from .utils.chat_formatting import pagify

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class Twitter:
    """Cog to get twitter feeds"""

    def __init__(self, bot, sleep):
        self.bot = bot
        self.sleep = sleep
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
    @checks.mod_or_permissions(administrator=True)
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

    @checks.is_owner()
    @_twitter.command(pass_context=True, no_pm=True, name="globallist")
    async def _globallist(self, ctx):
        """Lists all facebook users in the database"""
        server = ctx.message.server

        listMessage = ""
        for feed in self.feeds:
            feed_server = self.bot.get_server(feed["serverId"])
            listMessage += "#{1}: `@{0[userName]}` posting to <#{0[channelId]}> in `{2.name}`\n".format(feed, self.feeds.index(feed), feed_server)

        if listMessage == "":
            await self.bot.say("No user in database!")
            return

        for page in pagify("Found these users:\n{0}**Users total: {1}**".format(listMessage, len(self.feeds)), ["\n"]):
            if page != "":
                await self.bot.say(page)
                
    @_twitter.command(pass_context=True, no_pm=True, name="del")
    @checks.mod_or_permissions(administrator=True)
    async def _del(self, context, feedId : int):
        """Deletes an twitter user from the database"""
        server = context.message.server

        try:
            if self.feeds[feedId]["serverId"] != server.id:
                await self.bot.say("You can only delete entries from the server you are on!")
                return
        except IndexError:
            await self.bot.say("Entry not found in database!")
            return
        
        del(self.feeds[feedId])
        
        dataIO.save_json(self.feeds_file_path, self.feeds)

        await self.bot.say("User deleted from database")

    @_twitter.command(no_pm=True, name="force")
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

        await self._post_item(channel, twitterUserTimeline[0])

    async def _post_item(self, channel, item):
        data = self.get_embed_for_item(item)
        itemUrl = "https://twitter.com/statuses/{0}".format(item.id_str)

        await self.bot.send_message(channel, "<{0}>".format(itemUrl), embed=data)

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

    @_twitter.command(no_pm=True, name="refresh")
    async def _refresh(self):
        """Refreshes all twitter feeds manually"""
        nb_cancelled = self.sleep.cancel_all()
        await asyncio.wait(self.sleep.tasks)

        await self.bot.say("Done :ok_hand:")

    async def check_feed_loop(self, sleep, loop):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('Twitter'):
            print("checking twitter feed...")
            self.authenticate()
            for feed in self.feeds:
                channel = self.bot.get_channel(feed["channelId"])
                if channel == None:
                    print("Channel not found")
                    continue
                try:
                    if feed["lastId"] == 0:
                        twitterUserTimeline = self.twitterAPI.user_timeline(screen_name=feed["userName"], include_rts=True, exclude_replies=True)
                    else:
                        twitterUserTimeline = self.twitterAPI.user_timeline(screen_name=feed["userName"], include_rts=True, since_id=feed["lastId"], exclude_replies=True)
                except Exception:
                    print("something went wrong fetching twitter account")
                    continue

                if len(twitterUserTimeline) > 0:
                    self.feeds[self.feeds.index(feed)]["lastId"] = twitterUserTimeline[0].id
                    dataIO.save_json(self.feeds_file_path, self.feeds)

                for item in twitterUserTimeline:
                    await self._post_item(channel, item)
            await loop.create_task(sleep(600))

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

def make_sleep():
    async def sleep(delay, result=None, *, loop=None):
        coro = asyncio.sleep(delay, result=result, loop=loop)
        task = asyncio.ensure_future(coro)
        sleep.tasks.add(task)
        try:
            return await task
        except asyncio.CancelledError:
            return result
        finally:
            sleep.tasks.remove(task)

    sleep.tasks = set()
    sleep.cancel_all = lambda: sum(task.cancel() for task in sleep.tasks)
    return sleep

def setup(bot):
    sleep = make_sleep()
    loop = asyncio.get_event_loop()
    check_folders()
    check_files()
    n = Twitter(bot, sleep)
    bot.add_cog(n)
    bot.loop.create_task(n.check_feed_loop(sleep, loop))
