import discord
from discord.ext import commands
from cogs.utils.InstagramAPI import InstagramAPI
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO
import asyncio
from random import choice as randchoice
from .utils import checks

class Instagram:
    """Cog to get instagram feeds"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/instagram/settings.json"
        self.settings = dataIO.load_json(self.file_path)
        self.feeds_file_path = "data/instagram/feeds.json"
        self.feeds = dataIO.load_json(self.feeds_file_path)
        self.instagramAPI = InstagramAPI(self.settings["USERNAME"], self.settings["PASSWORD"])
        self.instagramAPI.login()

    @commands.group(pass_context=True, no_pm=True, name="instagram", aliases=["i"])
    async def _instagram(self, context):
        """Posts new instagram pictures in discord"""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_instagram.command(no_pm=True, name="add")
    @checks.serverowner_or_permissions(administrator=True)
    async def _add(self, username : str, channel : discord.Channel):
        """Adds a new instagram user feed to a channel"""

        if self.instagramAPI.searchUsername(username) == False:
            await self.bot.say("Something went wrong!")
            return

        userId = self.instagramAPI.LastJson["user"]["pk"]

        if self.instagramAPI.getUserFeed(userId) == False:
            await self.bot.say("Something went wrong!")
            return

        lastItemTimestamp = self.instagramAPI.LastJson["items"][0]["taken_at"]

        self.feeds.append({"userId": userId,
            "userName": username,
            "channelId" : channel.id,
            "serverId" : channel.server.id,
            "lastTimestamp": lastItemTimestamp})
        dataIO.save_json(self.feeds_file_path, self.feeds)

        await self.bot.say("Added user to database!")

    @_instagram.command(pass_context=True, no_pm=True, name="list")
    @checks.serverowner_or_permissions(administrator=True)
    async def _list(self, ctx):
        """Lists all instagram users in the database on this server"""
        server = ctx.message.server

        listMessage = ""
        for feed in self.feeds:
            if feed["serverId"] == server.id:
                listMessage += "#{1}: @{0[userName]} posting to <#{0[channelId]}>\n".format(feed, self.feeds.index(feed))

        if listMessage == "":
            await self.bot.say("No user in database!")
            return

        await self.bot.say("Found these users:\n{0}".format(listMessage))

    @_instagram.command(no_pm=True, name="del")
    @checks.serverowner_or_permissions(administrator=True)
    async def _del(self, feedId : int):
        """Deletes an instagram user from the database"""

        try:
            del(self.feeds[feedId])
        except IndexError:
            await self.bot.say("Entry not found in database!")
            return

        dataIO.save_json(self.feeds_file_path, self.feeds)

        await self.bot.say("User deleted from database")

    async def check_feed_loop(self):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('Instagram'):
            for feed in self.feeds:
                channel = self.bot.get_channel(feed["channelId"])
                if self.instagramAPI.getUserFeed(feed["userId"], minTimestamp=feed["lastTimestamp"]) == False:
                    await self.bot.send_message(channel,
                        "Something went wrong fetching @{0}'s instagram feed!".format(feed["userName"]))
                    continue
                for item in self.instagramAPI.LastJson["items"]:
                    colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
                    colour = int(colour, 16)

                    itemUserName = item["user"]["username"]
                    itemUserProfilepicture = item["user"]["profile_pic_url"]
                    itemCaption = item["caption"]["text"]
                    itemPicture = item["image_versions2"]["candidates"][0]["url"]
                    itemTakenAt = item["taken_at"]
                    itemUrl = "https://www.instagram.com/p/{0}/".format(item["code"])

                    data = discord.Embed(
                        description=itemCaption,
                        colour=discord.Colour(value=colour))
                    data.set_author(name=itemUserName, icon_url=itemUserProfilepicture, url=itemUrl)
                    data.set_image(url=itemPicture)

                    await self.bot.send_message(channel, embed=data)
                    if itemTakenAt > feed["lastTimestamp"]:
                        self.feeds[self.feeds.index(feed)]["lastTimestamp"] = itemTakenAt
                        dataIO.save_json(self.feeds_file_path, self.feeds)
            await asyncio.sleep(600)

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

def setup(bot):
    check_folders()
    check_files()
    n = Instagram(bot)
    bot.loop.create_task(n.check_feed_loop())
    bot.add_cog(n)