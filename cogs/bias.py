import asyncio
import os
from .utils.dataIO import dataIO
import discord
from discord.ext import commands
import random

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class Bias:
    """I assign bias roles"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/bias/settings.json"
        self.settings = dataIO.load_json(self.file_path)

    async def on_message(self, message):
        channel = message.channel
        author = message.author
        server = message.server

        if message.server is None:
            return

        if author == self.bot.user:
            return

        if not self.bot.user_allowed(message):
            return

        if self._is_command(message.content):
            return

        if message.channel.id not in self.settings["BIAS_CHANNELS"]:
            return

        message.content = message.content.strip().lower()
        if message.content[0] != "+" and message.content[0] != "-":
            return

        changingRoleAlias = message.content[1:].strip()
        if changingRoleAlias == "":
            return

        availableRoles = self.settings["BIAS_ASSIGNABLE_ROLES"]
        if changingRoleAlias in availableRoles:
            changingRole = self._role_from_string(server, availableRoles[changingRoleAlias])
            if changingRole is None:
                print("role not found")
                await self.bot.send_message(channel, "Something went wrong.")
                return

            if message.content[0] == "+":
                if changingRole in author.roles:
                    successMessage = await self.bot.send_message(channel, "{} you already got that role! :thinking:".format(author.mention))

                    await asyncio.sleep(10)
                    await self.bot.delete_message(message)
                    await self.bot.delete_message(successMessage)
                    return
                selfAssignableRoles = 0
                for role in author.roles:
                    if role.name in list(availableRoles.values()):
                        selfAssignableRoles += 1
                if selfAssignableRoles > self.settings["BIAS_MAX_ROLES"]-1:
                    successMessage = await self.bot.send_message(channel, "{} you already have enough roles! :warning:".format(author.mention))

                    await asyncio.sleep(10)
                    await self.bot.delete_message(message)
                    await self.bot.delete_message(successMessage)
                    return

            if message.content[0] == "-":
                if changingRole not in author.roles:
                    successMessage = await self.bot.send_message(channel, "{} you don't have that role! :thinking:".format(author.mention))

                    await asyncio.sleep(10)
                    await self.bot.delete_message(message)
                    await self.bot.delete_message(successMessage)
                    return

            try:
                randomEmoji = ""
                if message.content[0] == "+":
                    randomEmoji = random.choice([":clap:", ":thumbsup:", ":blush:", ":sparkles:"])
                    await self.bot.add_roles(author, changingRole)
                else:
                    randomEmoji = random.choice([":scream:", ":thumbsdown:", ":mask:", ":flushed:"])
                    await self.bot.remove_roles(author, changingRole)
                successMessage = await self.bot.send_message(channel, "{0} done! {1}".format(author.mention, randomEmoji))

                await asyncio.sleep(10)
                await self.bot.delete_message(message)
                await self.bot.delete_message(successMessage)
            except Exception as e:
                print(e)
                await self.bot.send_message(channel, "Something went wrong.")

    def _role_from_string(self, server, rolename, roles=None):
        if roles is None:
            roles = server.roles
        role = discord.utils.find(lambda r: r.name.lower() == rolename.lower(), roles)
        return role

    def _is_command(self, msg):
        for p in self.bot.command_prefix:
            if msg.startswith(p):
                return True
        return False

def check_folders():
    folders = ("data", "data/bias/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"BIAS_MAX_ROLES" : 3,
    "BIAS_ASSIGNABLE_ROLES": {
    "alias": "role"
    },
    "BIAS_CHANNELS": ["your channel"]
    }

    if not os.path.isfile("data/bias/settings.json"):
        print("Creating empty settings.json...")
        dataIO.save_json("data/bias/settings.json", settings)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Bias(bot))
