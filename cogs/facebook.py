import discord
from discord.ext import commands
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO
import asyncio
from random import choice as randchoice
from .utils import checks
import facebook

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class Facebook:
    """Cog to get facebook feeds"""

    def __init__(self, bot, sleep):
        self.bot = bot
        self.sleep = sleep
        self.file_path = "data/facebook/settings.json"
        self.settings = dataIO.load_json(self.file_path)
        self.feeds_file_path = "data/facebook/feeds.json"
        self.feeds = dataIO.load_json(self.feeds_file_path)

    def authenticate(self):
        self.graph = facebook.GraphAPI(self.settings["ACCESS_TOKEN"])

    @commands.group(pass_context=True, no_pm=True, name="facebook", aliases=["fb"])
    async def _facebook(self, context):
        """Posts new facebook posts in discord"""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_facebook.command(no_pm=True, name="add")
    @checks.mod_or_permissions(administrator=True)
    async def _add(self, username : str, channel : discord.Channel):
        """Adds a new facebook user feed to a channel"""
        self.authenticate()

        profile = self.graph.get_object(username)
        
        if "id" not in profile or profile["id"] == "":
            await self.bot.say("User not found!")
            return

        lastId = 0
        posts = self.graph.get_connections(profile['id'], 'posts', fields="id")

        if len(posts['data']) > 0:
            lastId = posts['data'][0]["id"]

        self.feeds.append({"userName": username,
            "userId" : profile["id"],
            "channelId" : channel.id,
            "serverId" : channel.server.id,
            "lastId": lastId})
        dataIO.save_json(self.feeds_file_path, self.feeds)

        await self.bot.say("Added user to database!")

    @_facebook.command(pass_context=True, no_pm=True, name="list")
    async def _list(self, ctx):
        """Lists all facebook users in the database on this server"""
        server = ctx.message.server

        listMessage = ""
        for feed in self.feeds:
            if feed["serverId"] == server.id:
                listMessage += "#{1}: `@{0[userName]}` posting to <#{0[channelId]}>\n".format(feed, self.feeds.index(feed))

        if listMessage == "":
            await self.bot.say("No user in database!")
            return

        await self.bot.say("Found these users:\n{0}".format(listMessage))

    @_facebook.command(pass_context=True, no_pm=True, name="del")
    @checks.mod_or_permissions(administrator=True)
    async def _del(self, context, feedId : int):
        """Deletes an facebook user from the database"""
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

    @_facebook.command(no_pm=True, name="force")
    async def _force(self, username : str, channel : discord.Channel):
        """Forces to print the latest facebook post"""
        self.authenticate()

        profile = self.graph.get_object(username, fields="id,name")
        picture = self.graph.get_connections(profile["id"], "picture", fields="url")
        posts = self.graph.get_connections(profile["id"], "posts", fields="message,from,picture,id,actions,child_attachments")

        if len(posts['data']) <= 0:
            await self.bot.say("No posts found!")
            return

        await self._post_item(channel, profile, picture, posts['data'][0])

    async def _post_item(self, channel, profile, picture, item):
        data = self._get_embed_for_item(profile, picture, item)
        postIdOnly = item["id"].replace("{0[from][id]}_".format(item), "")
        itemUrl = "https://www.facebook.com/{0[from][id]}/posts/{1}".format(item, postIdOnly)

        await self.bot.send_message(channel, "<{0}>".format(itemUrl), embed=data)

    def _get_embed_for_item(self, profile, picture, item):
        colour = int("3b5998", 16)

        itemUserFullname = profile["name"]
        itemUserProfilepicture = picture["url"]
        itemCaption = ""
        if "message" in item:
            itemCaption = item["message"]

        postIdOnly = item["id"].replace("{0[from][id]}_".format(item), "")
        itemUrl = "https://www.facebook.com/{0[from][id]}/posts/{1}".format(item, postIdOnly)
        if "action" in item:
            for action in item["actions"]:
                itemUrl = action["link"]
                break

        data = discord.Embed(
            description=itemCaption,
            colour=discord.Colour(value=colour))
        data.set_author(name="{0}".format(itemUserFullname), icon_url=itemUserProfilepicture, url=itemUrl)

        if "child_attachments" in item and len(item["child_attachments"]) > 0:
            for attachment in item["child_attachments"]:
                if "picture" in attachment and attachment["picture"] != "":
                    data.set_image(url=attachment["picture"])
                    break

        if "picture" in item:
            data.set_image(url=item["picture"])

        data.set_footer(text="via facebook")
        return data

    @_facebook.command(no_pm=True, name="refresh")
    async def _refresh(self):
        """Refreshes all facebook feeds manually"""
        nb_cancelled = self.sleep.cancel_all()
        await asyncio.wait(self.sleep.tasks)

        await self.bot.say("Done :ok_hand:")

    async def check_feed_loop(self, sleep, loop):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('Facebook'):
            print("checking facebook feed...")
            try:
                self.authenticate()
            except Exception as e:
                print("something went wrong authenticating to facebook:", e)
                await sleep(60)
                continue

            for feed in self.feeds:
                try:
                    profile = self.graph.get_object(id=feed["userId"], fields="id,name")
                    picture = self.graph.get_connections(profile["id"], "picture", fields="url")
                    channel = self.bot.get_channel(feed["channelId"])
                    posts = self.graph.get_connections(profile["id"], 'posts', fields="message,from,picture,id,actions,child_attachments")
                except Exception as e:
                    print("something went wrong fetching facebook account:", e)
                    continue

                if len(posts["data"]) > 0:
                    for item in posts["data"]:
                        if feed["lastId"] == item["id"]:
                            break

                        await self._post_item(channel, profile, picture, item)

                    if posts["data"][0]["id"] != self.feeds[self.feeds.index(feed)]["lastId"]:
                        self.feeds[self.feeds.index(feed)]["lastId"] = posts["data"][0]["id"]
                        dataIO.save_json(self.feeds_file_path, self.feeds)
            await loop.create_task(sleep(600))

def check_folders():
    folders = ("data", "data/facebook/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"ACCESS_TOKEN": "yourfacebookaccesstoken"}
    feeds = []

    if not os.path.isfile("data/facebook/settings.json"):
        print("Creating empty settings.json, please fill in details...")
        dataIO.save_json("data/facebook/settings.json", settings)
    if not os.path.isfile("data/facebook/feeds.json"):
        print("Creating empty feeds.json...")
        dataIO.save_json("data/facebook/feeds.json", feeds)

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
    n = Facebook(bot, sleep)
    bot.add_cog(n)
    bot.loop.create_task(n.check_feed_loop(sleep, loop))
