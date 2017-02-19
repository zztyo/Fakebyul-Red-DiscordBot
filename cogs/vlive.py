import discord
from discord.ext import commands
from __main__ import send_cmd_help
from bs4 import BeautifulSoup
import aiohttp
import re
import os
from .utils.dataIO import dataIO
import asyncio
from .utils import checks
from .utils.chat_formatting import pagify

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "1.0"

class Vlive:
    """Get VLive notifications and more"""

    def __init__(self, bot, sleep):
        self.bot = bot
        self.sleep = sleep
        self.file_path = "data/vlive/settings.json"
        self.settings = dataIO.load_json(self.file_path)
        self.channels_file_path = "data/vlive/channels.json"
        self.channels = dataIO.load_json(self.channels_file_path)
        self.main_base_url = "http://www.vlive.tv/{0}"
        self.channel_base_url = "http://channels.vlive.tv/{0}"
        self.api_base_url = "http://api.vfan.vlive.tv/{0}?app_id={1}&{2}"
        self.notice_base_url = "http://notice.vlive.tv/notice/list.json?channel_seq={0}"
        self.notice_friendly_url = "http://channels.vlive.tv/{0}/notice/{1}"
        self.celeb_friendly_url = "http://channels.vlive.tv/{0}/celeb/{1}"
        self.channel_id_regex = r"(http(s)?:\/\/channels.vlive.tv)?(\/)?(channels\/)?(?P<channel_id>[A-Z0-9]+)(\/video)?"
        self.headers = {"user-agent": "Red-cog-VLive/"+__version__}

    @commands.group(pass_context=True, no_pm=True, name="vlive", aliases=["vl"])
    async def _vlive(self, context):
        """VLive"""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_vlive.command(pass_context=True, no_pm=True, name="info")
    async def _info(self, context, channel_search_name : str):
        """Find out more about a vlive channel"""
        author = context.message.author

        await self.bot.type()

        # search for channel
        channel_id = await self.get_channel_id_from_channel_name(channel_search_name)
        if channel_id != None:
            channel_information = await self.get_channel_information_from_channel_id(channel_id)
            if channel_information != None:
                await self.bot.say("<{0}>".format(channel_information["channel_url"]), embed=self.get_channel_card_from_channel_information(channel_information))
                return
        # channel_search_name is channel_id instead?
        channel_information = await self.get_channel_information_from_channel_id(channel_search_name)
        if channel_information != None:
            await self.bot.say("<{0}>".format(channel_information["channel_url"]), embed=self.get_channel_card_from_channel_information(channel_information))
            return

        await self.bot.say("{0} Unable to find channel (CHANNEL+ channels get ignored).".format(author.mention))

    @_vlive.command(pass_context=True, no_pm=True, name="add")
    @checks.mod_or_permissions(administrator=True)
    async def _add(self, context, channel_search_name : str, post_channel : discord.Channel):
        """Adds a new vlive channel to a channel"""
        author = context.message.author
        channel = context.message.channel

        await self.bot.type()

        # search for channel
        channel_id = await self.get_channel_id_from_channel_name(channel_search_name)
        if channel_id != None:
            channel_information = await self.get_channel_information_from_channel_id(channel_id)
            if channel_information == None or channel_information["name"] == "":
                channel_id = None
        # channel_search_name is channel_id instead?
        if channel_id == None:
            channel_information = await self.get_channel_information_from_channel_id(channel_search_name)
            if channel_information != None:
                channel_id = channel_search_name

        if channel_id == None or channel_information == None or channel_information["name"] == "":
            await self.bot.say("{0} Unable to find channel (CHANNEL+ channels get ignored).".format(author.mention))
            return

        self.channels.append({"vliveChannelId": channel_id,
            "vliveChannelName": channel_information["name"],
            "lastVideoSeq" : channel_information["last_video"]["seq"],
            "lastUpcomingVideoSeq": channel_information["next_upcoming_video"]["seq"],
            "lastNoticeNumber": channel_information["last_notice"]["number"],
            "lastCelebPostId": channel_information["last_celeb_post"]["id"],
            "channelId" : post_channel.id,
            "serverId" : post_channel.server.id})
        dataIO.save_json(self.channels_file_path, self.channels)

        await self.bot.say("{0} Added channel \"{1}\" (`{2}`) to database!".format(author.mention, channel_information["name"], channel_id))

    @_vlive.command(pass_context=True, no_pm=True, name="list")
    async def _list(self, ctx):
        """Lists all vlive channels in the database on this server"""
        server = ctx.message.server

        listMessage = ""
        for channel in self.channels:
            if channel["serverId"] == server.id:
                listMessage += "#{1}: `{0[vliveChannelName]} ({0[vliveChannelId]})` posting to <#{0[channelId]}>\n".format(channel, self.channels.index(channel))

        if listMessage == "":
            await self.bot.say("No channels in database!")
            return

        await self.bot.say("Found these channels:\n{0}".format(listMessage))

    @checks.is_owner()
    @_vlive.command(pass_context=True, no_pm=True, name="globallist")
    async def _globallist(self, ctx):
        """Lists all vlive channels in the database"""
        server = ctx.message.server

        listMessage = ""
        for channel in self.channels:
            channel_server = self.bot.get_server(channel["serverId"])
            listMessage += "#{1}: `{0[vliveChannelName]} ({0[vliveChannelId]})` posting to <#{0[channelId]}> in `{2.name}`\n".format(channel, self.channels.index(channel), channel_server)

        if listMessage == "":
            await self.bot.say("No channels in database!")
            return

        for page in pagify("Found these channels:\n{0}**Channels total: {1}**".format(listMessage, len(self.channels)), ["\n"]):
            if page != "":
                await self.bot.say(page)

    @_vlive.command(pass_context=True, no_pm=True, name="del")
    @checks.mod_or_permissions(administrator=True)
    async def _del(self, context, channelId : int):
        """Deletes an vlive channel from the database"""
        server = context.message.server

        try:
            if self.channels[channelId]["serverId"] != server.id:
                await self.bot.say("You can only delete entries from the server you are on!")
                return
        except IndexError:
            await self.bot.say("Entry not found in database!")
            return
        
        del(self.channels[channelId])

        dataIO.save_json(self.channels_file_path, self.channels)

        await self.bot.say("Channel deleted from database")

    def get_channel_card_from_channel_information(self, channel_information):
        embed_data = discord.Embed(
            title="{0} V LIVE Channel".format(channel_information["name"]),
            url=channel_information["channel_url"],
            colour=discord.Colour(value=int(channel_information["color"].replace("#", ""), 16)))
        embed_data.add_field(name="Followers", value="{0:,}".format(channel_information["followers"]))
        embed_data.add_field(name="Videos", value="{0:,}".format(channel_information["total_videos"]))
        embed_data.set_thumbnail(url=str(channel_information["profile_img"]))
        embed_data.set_footer(text="via vlive.tv")

        if channel_information["next_upcoming_video"]["title"] != "":
            embed_data.add_field(inline=False, name="Next Upcoming Video on {0} KST".format(channel_information["next_upcoming_video"]["date"]), value="**{0}**\n**Likes** {1:,}\n{2}".format(channel_information["next_upcoming_video"]["title"], channel_information["next_upcoming_video"]["likes"], channel_information["next_upcoming_video"]["url"]))

        if channel_information["last_video"]["title"] != "":
            video_type_string = "Last Video on"
            if channel_information["last_video"]["type"] == "LIVE":
                video_type_string = ":mega: Currently Live since"
            embed_data.add_field(inline=False, name="{0} {1} KST".format(video_type_string, channel_information["last_video"]["date"]), value="**{0}**\n**Plays** {1:,}\n**Likes** {2:,}\n{3}".format(channel_information["last_video"]["title"], channel_information["last_video"]["plays"], channel_information["last_video"]["likes"], channel_information["last_video"]["url"]))
            embed_data.set_image(url=channel_information["last_video"]["thumbnail"])
        return embed_data

    async def get_channel_information_from_channel_id(self, channel_id):
        channel_seq = await self.get_channel_seq_from_channel_id(channel_id)

        channel_api_url = self.api_base_url.format("channel.{0}".format(channel_seq), self.settings["VLIVE_APP_ID"], "fields=channel_name,fan_count,channel_cover_img,channel_profile_img,representative_color,celeb_board")
        channel_video_list_api_url = self.api_base_url.format("vproxy/channelplus/getChannelVideoList", self.settings["VLIVE_APP_ID"], "channelSeq={0}&maxNumOfRows=1".format(channel_seq))
        channel_upcoming_video_list_api_url = self.api_base_url.format("vproxy/channelplus/getUpcomingVideoList", self.settings["VLIVE_APP_ID"], "channelSeq={0}&maxNumOfRows=1".format(channel_seq))
        channel_notices_api_url = self.notice_base_url.format(channel_seq)

        channel_data = {"name": "", "followers": 0, "cover_img": "", "profile_img": "", "color": "", "total_videos": 0, "celeb_board_id": 0,
        "last_video": {"seq": 0, "title": "", "plays": 0, "likes": 0, "thumbnail": "", "date": "", "type": ""},
        "next_upcoming_video": {"seq": 0, "title": "", "plays": 0, "likes": 0, "thumbnail": "", "date": "", "type": ""},
        "last_notice": {"number": 0, "image_url": "", "title": "", "summary": "", "url": ""},
        "last_celeb_post": {"id": "", "summary": "", "url": ""}}

        try:
            conn = aiohttp.TCPConnector()
            session = aiohttp.ClientSession(connector=conn)
            async with session.get(channel_api_url, headers=self.headers) as r:
                result = await r.json()

            if "error" in result:
                session.close()
                return None

            channel_data["name"] = result["channel_name"]
            channel_data["followers"] = result["fan_count"]
            channel_data["cover_img"] = result["channel_cover_img"]
            channel_data["profile_img"] = result["channel_profile_img"]
            channel_data["color"] = result["representative_color"]
            channel_data["channel_url"] = self.channel_base_url.format(channel_id)
            if "celeb_board" in result and "board_id" in result["celeb_board"]:
                channel_data["celeb_board_id"] = result["celeb_board"]["board_id"]

            async with session.get(channel_video_list_api_url, headers=self.headers) as r:
                result = await r.json()

            channel_data["total_videos"] = result["result"]["totalVideoCount"]

            if "videoList" in result["result"] and result["result"]["videoList"] != None and len(result["result"]["videoList"]) > 0:
                last_video = result["result"]["videoList"][0]
                channel_data["last_video"]["seq"] = last_video["videoSeq"]
                channel_data["last_video"]["title"] = last_video["title"]
                channel_data["last_video"]["plays"] = last_video["playCount"]
                channel_data["last_video"]["likes"] = last_video["likeCount"]
                if "thumbnail" in last_video:
                    channel_data["last_video"]["thumbnail"] = last_video["thumbnail"]
                channel_data["last_video"]["date"] = last_video["onAirStartAt"]
                channel_data["last_video"]["type"] = last_video["videoType"]
                channel_data["last_video"]["url"] = self.main_base_url.format("video/{0}".format(last_video["videoSeq"]))

            async with session.get(channel_upcoming_video_list_api_url, headers=self.headers) as r:
                result = await r.json()

            if "videoList" in result["result"] and result["result"]["videoList"] != None and len(result["result"]["videoList"]) > 0:
                next_upcoming_video = result["result"]["videoList"][0]
                channel_data["next_upcoming_video"]["seq"] = next_upcoming_video["videoSeq"]
                channel_data["next_upcoming_video"]["title"] = next_upcoming_video["title"]
                channel_data["next_upcoming_video"]["likes"] = next_upcoming_video["likeCount"]
                if "thumbnail" in next_upcoming_video:
                    channel_data["next_upcoming_video"]["thumbnail"] = next_upcoming_video["thumbnail"]
                channel_data["next_upcoming_video"]["date"] = next_upcoming_video["onAirStartAt"]
                channel_data["next_upcoming_video"]["type"] = next_upcoming_video["videoType"]
                channel_data["next_upcoming_video"]["url"] = self.main_base_url.format("video/{0}".format(next_upcoming_video["videoSeq"]))

            async with session.get(channel_notices_api_url, headers=self.headers) as r:
                result = await r.json()

            if "data" in result and len(result["data"]) > 0:
                last_notice = result["data"][0]
                channel_data["last_notice"]["number"] = last_notice["noticeNo"]
                channel_data["last_notice"]["title"] = last_notice["title"]
                channel_data["last_notice"]["image_url"] = last_notice["listImageUrl"]
                channel_data["last_notice"]["summary"] = last_notice["summary"]
                channel_data["last_notice"]["url"] = self.notice_friendly_url.format(channel_id, last_notice["noticeNo"])

            if channel_data["celeb_board_id"] != 0:
                channel_celeb_api_url = self.api_base_url.format("board.{0}/posts".format(channel_data["celeb_board_id"]), self.settings["VLIVE_APP_ID"], "")

                async with session.get(channel_celeb_api_url, headers=self.headers) as r:
                    result = await r.json()

                if "data" in result and len(result["data"]) > 0:
                    last_celeb_post = result["data"][0]
                    channel_data["last_celeb_post"]["id"] = last_celeb_post["post_id"]
                    channel_data["last_celeb_post"]["summary"] = last_celeb_post["body_summary"]
                    channel_data["last_celeb_post"]["url"] = self.celeb_friendly_url.format(channel_id, last_celeb_post["post_id"])

            session.close()

            return channel_data
        except Exception as e:
            self.bot.logger.error(e, exc_info=True)
            return None

    async def get_channel_seq_from_channel_id(self, channel_id):
        decode_channel_code_api_url = self.api_base_url.format("vproxy/channelplus/decodeChannelCode", self.settings["VLIVE_APP_ID"], "channelCode={0}".format(channel_id))

        try:
            conn = aiohttp.TCPConnector()
            session = aiohttp.ClientSession(connector=conn)
            async with session.get(decode_channel_code_api_url, headers=self.headers) as r:
                result = await r.json()
            session.close()
            return result["result"]["channelSeq"]
        except Exception as e:
            self.bot.logger.error(e, exc_info=True)
            return None

    async def get_channel_id_from_channel_name(self, channel_search_name):
        search_url = self.main_base_url.format("search/channels?query={0}".format(channel_search_name))

        try:
            async with aiohttp.get(search_url) as response:
                soup_object = BeautifulSoup(await response.text(), "html.parser")
            channels = soup_object.find_all(class_="ct_box")
            if channels != None and len(channels) > 0:
                for channel in channels: # skip plus channel
                    if not channel.find(class_="name").get_text().endswith(" +"):
                        break
                for channel in channels: # channel with the exact name?
                    if channel.find(class_="name").get_text().lower() == channel_search_name.lower():
                        break
                channel_url = channel.get("href")
                match = re.match(self.channel_id_regex, channel_url)
                channel_id = match.group("channel_id")
                return channel_id
            else:
                return None
        except Exception as e:
            self.bot.logger.error(e, exc_info=True)
            return None

    def is_int(self, s):
        try: 
            int(s)
            return True
        except ValueError:
            return False

    @_vlive.command(no_pm=True, name="refresh")
    async def _refresh(self):
        """Refreshes all vlive channels manually"""
        nb_cancelled = self.sleep.cancel_all()
        await asyncio.wait(self.sleep.tasks)

        await self.bot.say("Done :ok_hand:")

    async def _post_regular_item(self, channel, channel_information):
        embed_data = discord.Embed(
            title=":film_frames: {0} uploaded a new video!".format(channel_information["name"]),
            url=channel_information["last_video"]["url"],
            colour=discord.Colour(value=int(channel_information["color"].replace("#", ""), 16)),
            description=channel_information["last_video"]["title"])
        embed_data.set_thumbnail(url=str(channel_information["profile_img"]))
        embed_data.set_image(url=str(channel_information["last_video"]["thumbnail"]))
        embed_data.set_footer(text="via vlive.tv")
        #embed_data.add_field(name="Plays", value="{0:,}".format(channel_information["last_video"]["plays"]))
        #embed_data.add_field(name="Likes", value="{0:,}".format(channel_information["last_video"]["likes"]))

        await self.bot.send_message(channel, "<{0}>".format(channel_information["last_video"]["url"]), embed=embed_data)

    async def _post_live_item(self, channel, channel_information):
        embed_data = discord.Embed(
            title=":mega: {0} just went live!".format(channel_information["name"]),
            url=channel_information["last_video"]["url"],
            colour=discord.Colour(value=int(channel_information["color"].replace("#", ""), 16)),
            description=channel_information["last_video"]["title"])
        embed_data.set_thumbnail(url=str(channel_information["profile_img"]))
        embed_data.set_image(url=str(channel_information["last_video"]["thumbnail"]))
        embed_data.set_footer(text="via vlive.tv")
        #embed_data.add_field(name="Plays", value="{0:,}".format(channel_information["last_video"]["plays"]))
        #embed_data.add_field(name="Likes", value="{0:,}".format(channel_information["last_video"]["likes"]))

        await self.bot.send_message(channel, "<{0}>".format(channel_information["last_video"]["url"]), embed=embed_data)

    async def _post_upcoming_item(self, channel, channel_information):
        embed_data = discord.Embed(
            title=":calendar_spiral: {0} scheduled a new video for {1} KST!".format(channel_information["name"], channel_information["next_upcoming_video"]["date"]),
            url=channel_information["next_upcoming_video"]["url"],
            colour=discord.Colour(value=int(channel_information["color"].replace("#", ""), 16)),
            description=channel_information["next_upcoming_video"]["title"])
        embed_data.set_thumbnail(url=str(channel_information["profile_img"]))
        embed_data.set_image(url=str(channel_information["next_upcoming_video"]["thumbnail"]))
        embed_data.set_footer(text="via vlive.tv")
        #embed_data.add_field(name="Plays", value="{0:,}".format(channel_information["next_upcoming_video"]["plays"]))
        #embed_data.add_field(name="Likes", value="{0:,}".format(channel_information["next_upcoming_video"]["likes"]))

        await self.bot.send_message(channel, "<{0}>".format(channel_information["next_upcoming_video"]["url"]), embed=embed_data)

    async def _post_notice(self, channel, channel_information):
        embed_data = discord.Embed(
            title=":pencil: {0} posted a new notice!".format(channel_information["name"]),
            url=channel_information["last_notice"]["url"],
            colour=discord.Colour(value=int(channel_information["color"].replace("#", ""), 16)),
            description="**{0}**\n{1}".format(channel_information["last_notice"]["title"], channel_information["last_notice"]["summary"]))
        embed_data.set_thumbnail(url=str(channel_information["profile_img"]))
        embed_data.set_image(url=str(channel_information["last_notice"]["image_url"]))
        embed_data.set_footer(text="via vlive.tv")

        await self.bot.send_message(channel, "<{0}>".format(channel_information["last_notice"]["url"]), embed=embed_data)

    async def _post_celebpost(self, channel, channel_information):
        embed_data = discord.Embed(
            title=":star2: {0} posted a new celeb post!".format(channel_information["name"]),
            url=channel_information["last_celeb_post"]["url"],
            colour=discord.Colour(value=int(channel_information["color"].replace("#", ""), 16)),
            description="{0}".format(channel_information["last_celeb_post"]["summary"]))
        embed_data.set_thumbnail(url=str(channel_information["profile_img"]))
        embed_data.set_footer(text="via vlive.tv")

        await self.bot.send_message(channel, "<{0}>".format(channel_information["last_celeb_post"]["url"]), embed=embed_data)

    async def check_feed_loop(self, sleep, loop):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('Vlive'):
            print("checking vlive channels...")
            for vlive_channel in self.channels:
                channel = self.bot.get_channel(vlive_channel["channelId"])
                if channel == None:
                    print("Channel not found")
                    continue
                channel_information = await self.get_channel_information_from_channel_id(vlive_channel["vliveChannelId"])

                if "lastVideoSeq" not in vlive_channel or channel_information["last_video"]["seq"] != vlive_channel["lastVideoSeq"]:
                    if "lastVideoSeq" in vlive_channel and channel_information["last_video"]["seq"] != 0:
                        if channel_information["last_video"]["type"] == "LIVE":
                            await self._post_live_item(channel, channel_information)
                        else:
                            await self._post_regular_item(channel, channel_information)

                    self.channels[self.channels.index(vlive_channel)]["lastVideoSeq"] = channel_information["last_video"]["seq"]
                    dataIO.save_json(self.channels_file_path, self.channels)

                if "lastUpcomingVideoSeq" not in vlive_channel or channel_information["next_upcoming_video"]["seq"] != vlive_channel["lastUpcomingVideoSeq"]:
                    if "lastUpcomingVideoSeq" in vlive_channel and channel_information["next_upcoming_video"]["seq"] != 0:
                        await self._post_upcoming_item(channel, channel_information)

                    self.channels[self.channels.index(vlive_channel)]["lastUpcomingVideoSeq"] = channel_information["next_upcoming_video"]["seq"]
                    dataIO.save_json(self.channels_file_path, self.channels)

                if "lastNoticeNumber" not in vlive_channel or channel_information["last_notice"]["number"] != vlive_channel["lastNoticeNumber"]:
                    if "lastNoticeNumber" in vlive_channel and channel_information["last_notice"]["number"] != 0:
                        await self._post_notice(channel, channel_information)

                    self.channels[self.channels.index(vlive_channel)]["lastNoticeNumber"] = channel_information["last_notice"]["number"]
                    dataIO.save_json(self.channels_file_path, self.channels)

                if "lastCelebPostId" not in vlive_channel or channel_information["last_celeb_post"]["id"] != vlive_channel["lastCelebPostId"]:
                    if "lastCelebPostId" in vlive_channel and channel_information["last_celeb_post"]["id"] != "":
                        await self._post_celebpost(channel, channel_information)

                    self.channels[self.channels.index(vlive_channel)]["lastCelebPostId"] = channel_information["last_celeb_post"]["id"]
                    dataIO.save_json(self.channels_file_path, self.channels)

            await loop.create_task(sleep(60))

def check_folders():
    folders = ("data", "data/vlive/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"VLIVE_APP_ID": "yourvliveappid",}
    channels = []

    if not os.path.isfile("data/vlive/settings.json"):
        print("Creating empty settings.json, please fill in details...")
        dataIO.save_json("data/vlive/settings.json", settings)
    if not os.path.isfile("data/vlive/channels.json"):
        print("Creating empty channels.json...")
        dataIO.save_json("data/vlive/channels.json", channels)

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
    n = Vlive(bot, sleep)
    bot.add_cog(n)
    bot.loop.create_task(n.check_feed_loop(sleep, loop))