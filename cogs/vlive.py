import discord
from discord.ext import commands
from __main__ import send_cmd_help
from bs4 import BeautifulSoup
import aiohttp
import re
import os
from .utils.dataIO import dataIO

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class Vlive:
    """Get VLive notifications and more"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/vlive/settings.json"
        self.settings = dataIO.load_json(self.file_path)
        self.main_base_url = "http://www.vlive.tv/{0}"
        self.channel_base_url = "http://channels.vlive.tv/{0}/video"
        self.api_base_url = "http://api.vfan.vlive.tv/{0}?app_id={1}&{2}"
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

    def get_channel_card_from_channel_information(self, channel_information):
        embedData = discord.Embed(
            title="{0} V LIVE Channel".format(channel_information["name"]),
            url=channel_information["channel_url"],
            colour=discord.Colour(value=int(channel_information["color"].replace("#", ""), 16)))
        embedData.add_field(name="Followers", value="{0:,}".format(channel_information["followers"]))
        embedData.add_field(name="Videos", value="{0:,}".format(channel_information["total_videos"]))
        embedData.set_thumbnail(url=str(channel_information["profile_img"]))
        embedData.set_footer(text="via vlive.tv")

        if channel_information["next_upcoming_video"]["title"] != "":
            embedData.add_field(inline=False, name="Next Upcoming Video {0} KST".format(channel_information["next_upcoming_video"]["date"]), value="**{0}**\n**Likes** {1:,}\n{2}".format(channel_information["next_upcoming_video"]["title"], channel_information["next_upcoming_video"]["likes"], channel_information["next_upcoming_video"]["url"]))

        if channel_information["last_video"]["title"] != "":
            embedData.add_field(inline=False, name="Last Video on {0} KST".format(channel_information["last_video"]["date"]), value="**{0}**\n**Plays** {1:,}\n**Likes** {2:,}\n{3}".format(channel_information["last_video"]["title"], channel_information["last_video"]["plays"], channel_information["last_video"]["likes"], channel_information["last_video"]["url"]))
            embedData.set_image(url=channel_information["last_video"]["thumbnail"])
        return embedData

    async def get_channel_information_from_channel_id(self, channel_id):
        channel_seq = await self.get_channel_seq_from_channel_id(channel_id)

        channel_api_url = self.api_base_url.format("channel.{0}".format(channel_seq), self.settings["VLIVE_APP_ID"], "fields=channel_name,fan_count,channel_cover_img,channel_profile_img,representative_color")
        channel_video_list_api_url = self.api_base_url.format("vproxy/channelplus/getChannelVideoList", self.settings["VLIVE_APP_ID"], "channelSeq={0}&maxNumOfRows=1".format(channel_seq))
        channel_upcoming_video_list_api_url = self.api_base_url.format("vproxy/channelplus/getUpcomingVideoList", self.settings["VLIVE_APP_ID"], "channelSeq={0}&maxNumOfRows=1".format(channel_seq))

        channel_data = {"name": "", "followers": 0, "cover_img": "", "profile_img": "", "color": "", "total_videos": 0,
        "last_video": {"seq": "", "title": "", "plays": 0, "likes": 0, "thumbnail": "", "date": ""},
        "next_upcoming_video": {"seq": "", "title": "", "plays": 0, "likes": 0, "thumbnail": "", "date": ""}}

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

            async with session.get(channel_video_list_api_url, headers=self.headers) as r:
                result = await r.json()

            channel_data["total_videos"] = result["result"]["totalVideoCount"]

            if "videoList" in result["result"] and result["result"]["videoList"] != None and len(result["result"]["videoList"]) > 0:
                last_video = result["result"]["videoList"][0]
                channel_data["last_video"]["seq"] = last_video["videoSeq"]
                channel_data["last_video"]["title"] = last_video["title"]
                channel_data["last_video"]["plays"] = last_video["playCount"]
                channel_data["last_video"]["likes"] = last_video["likeCount"]
                channel_data["last_video"]["thumbnail"] = last_video["thumbnail"]
                channel_data["last_video"]["date"] = last_video["onAirStartAt"]
                channel_data["last_video"]["url"] = self.main_base_url.format("video/{0}".format(last_video["videoSeq"]))

            async with session.get(channel_upcoming_video_list_api_url, headers=self.headers) as r:
                result = await r.json()

            if "videoList" in result["result"] and result["result"]["videoList"] != None and len(result["result"]["videoList"]) > 0:
                next_upcoming_video = result["result"]["videoList"][0]
                channel_data["next_upcoming_video"]["seq"] = next_upcoming_video["videoSeq"]
                channel_data["next_upcoming_video"]["title"] = next_upcoming_video["title"]
                channel_data["next_upcoming_video"]["likes"] = next_upcoming_video["likeCount"]
                channel_data["next_upcoming_video"]["thumbnail"] = next_upcoming_video["thumbnail"]
                channel_data["next_upcoming_video"]["date"] = next_upcoming_video["onAirStartAt"]
                channel_data["next_upcoming_video"]["url"] = self.main_base_url.format("video/{0}".format(next_upcoming_video["videoSeq"]))

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

def check_folders():
    folders = ("data", "data/vlive/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"VLIVE_APP_ID": "yourvliveappid",}
    feeds = []

    if not os.path.isfile("data/vlive/settings.json"):
        print("Creating empty settings.json, please fill in details...")
        dataIO.save_json("data/vlive/settings.json", settings)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Vlive(bot))