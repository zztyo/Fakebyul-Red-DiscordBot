import discord
from discord.ext import commands
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO
from .utils import checks
import re
import aiohttp
import json

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "1.0"

class Mirror:
    """Mirrors discord chats between servers!"""

    def __init__(self, bot):
        self.bot = bot
        self.mirrored_channels_file_path = "data/mirror/mirrored_channels.json"
        self.mirrored_channels = dataIO.load_json(self.mirrored_channels_file_path)

    # @commands.group(pass_context=True, no_pm=True, name="mirror")
    # @checks.mod_or_permissions(administrator=True)
    # async def _mirror(self, context):
    #     """Manages mirrored channels"""
    #     if context.invoked_subcommand is None:
    #         await send_cmd_help(context)

    async def mirror_message(self, message):
        server = message.server
        author = message.author
        channel = message.channel

        if message.server is None:
            return

        if message.channel.is_private:
            return

        if author == self.bot.user:
            return

        if self._is_command(message.content):
            return

        for mirrored_channel_entry in self.mirrored_channels:
            channel_gets_mirrored = False
            for mirrored_channel in mirrored_channel_entry["channels"]:
                if channel.id == mirrored_channel["channel_id"]:
                    channel_gets_mirrored = True
            if channel_gets_mirrored == False:
                continue
            if mirrored_channel_entry["mode"] == "media":
                links = []
                if len(message.attachments) > 0:
                    for attachment in message.attachments:
                        links.append(attachment["url"])
                if len(message.content) > 0:
                    if "http" in message.content:
                        for item in message.content.split(" "):
                            linksFound = re.findall("(?P<url><?https?://[^\s]+>?)", item)
                            if linksFound != None:
                                for linkFound in linksFound:
                                    if not (linkFound[0] == "<" and linkFound[len(linkFound)-1] == ">"):
                                        if linkFound[0] == "<":
                                            links.append(linkFound[1:len(linkFound)])
                                        else:
                                            links.append(linkFound)

                if len(links) > 0:
                    channels_to_mirror_to = []
                    for mirrored_channel in mirrored_channel_entry["channels"]:
                        if channel.id != mirrored_channel["channel_id"]:
                            channels_to_mirror_to.append(mirrored_channel)

                    for target_channel_data in channels_to_mirror_to:
                        for link in links:
                            target_channel = self.bot.get_channel(mirrored_channel["channel_id"])
                            if target_channel != None:
                                message = "posted {0} in the #{1.name} channel on the {1.server.name} discord ({1.mention})".format(link, channel)
                                await self._post_mirrored_message(message, author, channel, target_channel_data["webhook_id"], target_channel_data["webhook_token"])

    async def _post_mirrored_message(self, message, author, source_channel, target_webhook_id, target_webhook_token):
        headers = {"user-agent": "Red-cog-Mirror/"+__version__, "content-type": "application/json"}
        # use webhook
        conn = aiohttp.TCPConnector(verify_ssl=False)
        session = aiohttp.ClientSession(connector=conn)
        url = "https://discordapp.com/api/webhooks/{0}/{1}".format(target_webhook_id, target_webhook_token)
        payload = {"username": author.name, "avatar_url": author.avatar_url, "content": message}
        async with session.post(url, data=json.dumps(payload), headers=headers) as r:
            result = await r.text()
        if result != "":
            print("mirroring message webhook unexpected result:", result)
        session.close()

    def _is_command(self, msg):
        for p in self.bot.settings.prefixes:
            if msg.startswith(p):
                return True
        return False

def check_folders():
    folders = ("data", "data/mirror/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    mirrored_channels = []

    if not os.path.isfile("data/mirror/mirrored_channels.json"):
        print("Creating empty mirrored_channels.json, please fill in details...")
        dataIO.save_json("data/mirror/mirrored_channels.json", mirrored_channels)

def setup(bot):
    check_folders()
    check_files()
    n = Mirror(bot)
    bot.add_listener(n.mirror_message, "on_message")
    bot.add_cog(n)