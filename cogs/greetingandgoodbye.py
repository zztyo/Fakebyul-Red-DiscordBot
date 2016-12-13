import discord
import os
from .utils.dataIO import dataIO
from discord.ext import commands

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class Greetingandgoodbye:
    """My custom cog that does stuff!"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/greetingandgoodbye/settings.json"
        self.settings = dataIO.load_json(self.file_path)

    async def member_join(self, member):
        server = member.server
        if server != None and server.id in self.settings:
            serverSettings = self.settings[server.id]
            try:
                channel = server.get_channel(serverSettings["CHANNEL"])
            except:
                return None
            await self.bot.send_message(channel, serverSettings["GREETING"].format(member))

    async def member_remove(self, member):
        server = member.server
        if server != None and server.id in self.settings:
            serverSettings = self.settings[server.id]
            try:
                channel = server.get_channel(serverSettings["CHANNEL"])
            except:
                return None
            await self.bot.send_message(channel, serverSettings["GOODBYE"].format(member))

def check_folders():
    folders = ("data", "data/greetingandgoodbye/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"<SERVER ID>" : {
    "CHANNEL": "<CHANNEL ID>",
    "GREETING": "Welcome {0.mention}! :clap:",
    "GOODBYE": "Goodbye {0.name}! :wave:"
    },
    }

    if not os.path.isfile("data/greetingandgoodbye/settings.json"):
        print("Creating empty settings.json...")
        dataIO.save_json("data/greetingandgoodbye/settings.json", settings)

def setup(bot):
    check_folders()
    check_files()
    n = Greetingandgoodbye(bot)
    bot.add_listener(n.member_join,"on_member_join")
    bot.add_listener(n.member_remove,"on_member_remove")
    bot.add_cog(n)
