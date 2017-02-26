import discord
import os
from .utils.dataIO import dataIO
from discord.ext import commands
from cogs.utils import checks

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "1.0"

class Greetingandgoodbye:
    """Shows welcome and goodbye messages!"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/greetingandgoodbye/settings.json"
        self.settings = dataIO.load_json(self.file_path)

    @commands.command(pass_context=True, no_pm=True, name='toggle-greeting')
    @checks.mod_or_permissions(administrator=True)
    async def _toggle_greeting(self, ctx):
        """Toggles the greeting message"""
        server = ctx.message.server
        if server == None or server.id not in self.settings:
            await self.bot.say("Server not found!")
            return
        serverSettings = self.settings[server.id]
        postGreeting = True
        if "POST_GREETING" in serverSettings and serverSettings["POST_GREETING"] == False:
            postGreeting = False
        postGreeting = not postGreeting
        self.settings[server.id]["POST_GREETING"] = postGreeting
        dataIO.save_json(self.file_path, self.settings)
        if postGreeting == True:
            await self.bot.say("I will post a greeting when a user joins!")
        else:
            await self.bot.say("I will **not** post a greeting when a user joins!")

    @commands.command(pass_context=True, no_pm=True, name='toggle-goodbye')
    @checks.mod_or_permissions(administrator=True)
    async def _toggle_goodbye(self, ctx):
        """Toggles the goodbye message"""
        server = ctx.message.server
        if server == None or server.id not in self.settings:
            await self.bot.say("Server not found!")
            return
        serverSettings = self.settings[server.id]
        postGoodbye = True
        if "POST_GOODBYE" in serverSettings and serverSettings["POST_GOODBYE"] == False:
            postGoodbye = False
        postGoodbye = not postGoodbye
        self.settings[server.id]["POST_GOODBYE"] = postGoodbye
        dataIO.save_json(self.file_path, self.settings)
        if postGoodbye == True:
            await self.bot.say("I will post a goodbye when a user leaves!")
        else:
            await self.bot.say("I will **not** post a goodbye when a user leaves!")

    async def member_join(self, member):
        server = member.server
        if server != None and server.id in self.settings:
            serverSettings = self.settings[server.id]
            postGreeting = True
            if "POST_GREETING" in serverSettings and serverSettings["POST_GREETING"] == False:
                postGreeting = False
            if postGreeting == True:
                try:
                    channel = server.get_channel(serverSettings["CHANNEL"])
                except:
                    return None
                await self.bot.send_message(channel, serverSettings["GREETING"].format(member))
            if "DEFAULT_ROLE" in serverSettings:
                roles=server.roles
                rolename=serverSettings["DEFAULT_ROLE"].strip().replace("name ","")
                role = discord.utils.find(lambda r: r.name.lower() == rolename.lower(), roles)
                try:
                    await self.bot.add_roles(member, role)
                except Exception as e:
                    print(e)

    async def member_remove(self, member):
        server = member.server
        if server != None and server.id in self.settings:
            serverSettings = self.settings[server.id]
            postGoodbye = True
            if "POST_GOODBYE" in serverSettings and serverSettings["POST_GOODBYE"] == False:
                postGoodbye = False
            if postGoodbye == True:
                try:
                    channel = server.get_channel(serverSettings["CHANNEL"])
                except:
                    return None
                await self.bot.send_message(channel, serverSettings["GOODBYE"].format(member))

    @commands.command(pass_context=True, no_pm=True, name='defaultrole')
    @checks.mod_or_permissions(administrator=True)
    async def _default_role(self, ctx, *, text):
        '''Sets the default role that all new members get when they join'''
        server=ctx.message.server
        if server.id in self.settings:
            glist=self.settings[server.id]
            glist["DEFAULT_ROLE"] = text
            self.settings[server.id]=glist
            dataIO.save_json(self.file_path, self.settings)
            await self.bot.say("Default role successfully set.")
        
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
    "GOODBYE": "Goodbye {0.name}! :wave:",
    "POST_GREETING": True,
    "POST_GOODBYE": True,
    "DEFAULT_ROLE":""
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
