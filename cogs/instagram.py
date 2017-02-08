import discord
from discord.ext import commands
from cogs.utils.InstagramAPI import InstagramAPI
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO
import asyncio
from random import choice as randchoice
from .utils import checks
from .utils.chat_formatting import pagify

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "1.0"

class Instagram:
    """Cog to get instagram feeds"""

    def __init__(self, bot, sleep):
        self.bot = bot
        self.sleep = sleep
        self.file_path = "data/instagram/settings.json"
        self.settings = dataIO.load_json(self.file_path)
        self.feeds_file_path = "data/instagram/feeds.json"
        self.feeds = dataIO.load_json(self.feeds_file_path)
        self.instagramAPI = InstagramAPI(self.settings["USERNAME"], self.settings["PASSWORD"])

    @commands.group(pass_context=True, no_pm=True, name="instagram", aliases=["i"])
    async def _instagram(self, context):
        """Posts new instagram pictures in discord"""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_instagram.command(no_pm=True, name="add")
    @checks.mod_or_permissions(administrator=True)
    async def _add(self, username : str, channel : discord.Channel):
        """Adds a new instagram user feed to a channel"""

        await self.instagramAPI.login()
        if await self.instagramAPI.searchUsername(username) == False:
            await self.bot.say("Something went wrong!")
            return

        userId = self.instagramAPI.LastJson["user"]["pk"]

        if await self.instagramAPI.getUserFeed(userId) == False:
            await self.bot.say("Something went wrong!")
            return

        lastItemTimestamp = 0
        if "items" in self.instagramAPI.LastJson and len(self.instagramAPI.LastJson["items"]) > 0:
            lastItemTimestamp = self.instagramAPI.LastJson["items"][0]["taken_at"]

        self.feeds.append({"userId": userId,
            "userName": username,
            "channelId" : channel.id,
            "serverId" : channel.server.id,
            "lastTimestamp": lastItemTimestamp})
        dataIO.save_json(self.feeds_file_path, self.feeds)

        await self.bot.say("Added user to database!")

    @_instagram.command(pass_context=True, no_pm=True, name="list")
    async def _list(self, ctx):
        """Lists all instagram users in the database on this server"""
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
    @_instagram.command(pass_context=True, no_pm=True, name="globallist")
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
                
    @_instagram.command(pass_context=True, no_pm=True, name="del")
    @checks.mod_or_permissions(administrator=True)
    async def _del(self, context, feedId : int):
        """Deletes an instagram user from the database"""
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

    @_instagram.command(no_pm=True, name="force")
    async def _force(self, username : str, channel : discord.Channel):
        """Forces to print the latest instagram post"""

        await self.instagramAPI.login()
        if await self.instagramAPI.searchUsername(username) == False:
            await self.bot.say("Something went wrong!")
            return

        userId = self.instagramAPI.LastJson["user"]["pk"]

        if await self.instagramAPI.getUserFeed(userId) == False:
            await self.bot.say("Something went wrong!")
            return

        if "items" in self.instagramAPI.LastJson and len(self.instagramAPI.LastJson["items"]) > 0:
            await self._post_item(channel, self.instagramAPI.LastJson["items"][0])
        else:
            await self.bot.say("User has no posts")

    @_instagram.command(no_pm=True, name="refresh")
    async def _refresh(self):
        """Refreshes all instagram feeds manually"""
        nb_cancelled = self.sleep.cancel_all()
        await asyncio.wait(self.sleep.tasks)

        await self.bot.say("Done :ok_hand:")

    async def check_feed_loop(self, sleep, loop):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('Instagram'):
            print("checking instagram feed...")
            await self.instagramAPI.login()
            for feed in self.feeds:
                channel = self.bot.get_channel(feed["channelId"])
                if channel == None:
                    print("Channel not found")
                    continue
                if await self.instagramAPI.getUserFeed(feed["userId"], minTimestamp=feed["lastTimestamp"]) == False:
                    print("Something went wrong fetching @{0}'s instagram feed!".format(feed["userName"]))
                    continue
                if "items" in self.instagramAPI.LastJson:
                    for item in self.instagramAPI.LastJson["items"]:
                        await self._post_item(channel, item)
                        if item["taken_at"] > feed["lastTimestamp"]:
                            self.feeds[self.feeds.index(feed)]["lastTimestamp"] = item["taken_at"]
                            dataIO.save_json(self.feeds_file_path, self.feeds)
            await loop.create_task(sleep(600))

    async def _post_item(self, channel, item):
        data = self.get_embed_for_item(item)
        itemUrl = "https://www.instagram.com/p/{0}/".format(item["code"])

        await self.bot.send_message(channel, "<{0}>".format(itemUrl), embed=data)

    def get_embed_for_item(self, item):
        colour = int("F56040", 16)

        itemUserName = item["user"]["username"]
        itemUserProfilepicture = item["user"]["profile_pic_url"]
        itemCaption = ""
        if item["caption"] != None:
            itemCaption = item["caption"]["text"]
        itemPicture = item["image_versions2"]["candidates"][0]["url"]
        itemUrl = "https://www.instagram.com/p/{0}/".format(item["code"])
        if "video_versions" in item and len(item["video_versions"]) > 0:
            itemUserName += " (Video 🎞)"

        data = discord.Embed(
            description=itemCaption,
            colour=discord.Colour(value=colour))
        data.set_author(name=itemUserName, icon_url=itemUserProfilepicture, url=itemUrl)
        data.set_image(url=itemPicture)
        data.set_footer(text="via instagram")
        return data

def check_folders():
    folders = ("data", "data/instagram/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"USERNAME": "yourinstagramusername", "PASSWORD" : "yourinstagrampassword"}
    feeds = []

    if not os.path.isfile("data/instagram/settings.json"):
        print("Creating empty settings.json, please fill in details...")
        dataIO.save_json("data/instagram/settings.json", settings)
    if not os.path.isfile("data/instagram/feeds.json"):
        print("Creating empty feeds.json...")
        dataIO.save_json("data/instagram/feeds.json", feeds)

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
    n = Instagram(bot, sleep)
    bot.add_cog(n)
    bot.loop.create_task(n.check_feed_loop(sleep, loop))
