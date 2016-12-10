import asyncio
import os
from .utils.dataIO import dataIO
import discord
from discord.ext import commands
import random
from .utils import checks
from collections import OrderedDict
import json
import re

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class Bias:
    """I assign bias roles"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/bias/settings.json"
        self.settings = dataIO.load_json(self.file_path)

    @commands.command(pass_context=True, no_pm=True, name="bias-help")
    @checks.serverowner_or_permissions(administrator=True)
    async def bias_help(self, ctx):
        """Prints a help message with the bias list"""
        message = ctx.message
        channel = message.channel
        server = message.server

        if server.id not in self.settings:
            return

        aliasToPrint = []
        rolesHandled = []

        with open(self.file_path, encoding='utf-8', mode="r") as f:
            orderedSettings = json.load(f, object_pairs_hook=OrderedDict)
        helpMessage = "Use `+name` to add or `-name` to remove a bias role."
        if self.settings[server.id]["MAX_ROLES"] > 1:
            helpMessage += " You can have up to {0} {1}.".format(self._num_to_words(self.settings[server.id]["MAX_ROLES"]), "biases" if self.settings[server.id]["MAX_ROLES"] > 1 else "bias")
        helpMessage += "\nAvailable biases: "
        example = ""
        for alias, role in orderedSettings[server.id]["ASSIGNABLE_ROLES"].items():
            if role not in rolesHandled:
                rolesHandled.append(role)
                alias = str(alias).title()
                if re.match(r"^Ot[0-9]+$", alias):
                    alias = alias.replace("Ot", "OT")
                aliasToPrint.append(alias)
        i = 0
        for role in aliasToPrint:
            i += 1
            if i == 1:
                helpMessage += "`{0}`".format(role)
                example = "\nExample: `+{0}` or `-{0}`".format(role)
            elif i < len(aliasToPrint):
                helpMessage += ", `{0}`".format(role)
            else:
                helpMessage += " and `{0}`".format(role)
        helpMessage += "."
        helpMessage += example

        await self.bot.send_message(channel, helpMessage)


    async def check_message(self, message):
        channel = message.channel
        author = message.author
        server = message.server

        if message.server is None:
            return

        if author == self.bot.user:
            return

        if not self.bot.user_allowed(message):
            return

        if server.id not in self.settings:
            return

        if message.channel.id not in self.settings[server.id]["CHANNELS"]:
            return

        if message.author is self.bot.user:
            return

        if self._is_command(message.content):
            await asyncio.sleep(10)
            await self.bot.delete_message(message)
            return

        message.content = message.content.strip().lower()
        if message.content[0] != "+" and message.content[0] != "-":
            await asyncio.sleep(10)
            await self.bot.delete_message(message)
            return

        changingRoleAlias = message.content[1:].strip()
        if changingRoleAlias == "":
            return

        availableRoles = self.settings[server.id]["ASSIGNABLE_ROLES"]
        if changingRoleAlias not in availableRoles:
            successMessage = await self.bot.send_message(channel, "{} I can't find this bias role! :thinking:".format(author.mention))

            await asyncio.sleep(10)
            await self.bot.delete_message(successMessage)
            await self.bot.delete_message(message)
            return

        changingRole = self._role_from_string(server, availableRoles[changingRoleAlias])
        if changingRole is None:
            print("role not found")
            somethingWentWrong = await self.bot.send_message(channel, "Something went wrong.")

            await asyncio.sleep(10)
            await self.bot.delete_message(somethingWentWrong)
            await self.bot.delete_message(message)
            return

        if message.content[0] == "+":
            if changingRole in author.roles:
                successMessage = await self.bot.send_message(channel, "{} you already got this bias role! :thinking:".format(author.mention))

                await asyncio.sleep(10)
                await self.bot.delete_message(successMessage)
                await self.bot.delete_message(message)
                return
            selfAssignableRoles = 0
            for role in author.roles:
                if role.name in list(availableRoles.values()):
                    selfAssignableRoles += 1
            if selfAssignableRoles > self.settings[server.id]["MAX_ROLES"]-1:
                successMessage = await self.bot.send_message(channel, "{} you already have enough bias roles! :warning:".format(author.mention))

                await asyncio.sleep(10)
                await self.bot.delete_message(successMessage)
                await self.bot.delete_message(message)
                return

        if message.content[0] == "-":
            if changingRole not in author.roles:
                successMessage = await self.bot.send_message(channel, "{} you don't have this bias role! :thinking:".format(author.mention))

                await asyncio.sleep(10)
                await self.bot.delete_message(successMessage)
                await self.bot.delete_message(message)
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
        except Exception as e:
            print(e)
            somethingWentWrong = await self.bot.send_message(channel, "Something went wrong.")
            await asyncio.sleep(10)
            await self.bot.delete_message(somethingWentWrong)
            await self.bot.delete_message(message)
            return
        
        await asyncio.sleep(10)
        try:
            await self.bot.delete_message(successMessage)
            await self.bot.delete_message(message)
        except Exception:
            print(e)

    def _role_from_string(self, server, rolename, roles=None):
        if roles is None:
            roles = server.roles
        role = discord.utils.find(lambda r: r.name.lower() == rolename.lower(), roles)
        return role

    def _is_command(self, msg):
        for p in self.bot.settings.prefixes:
            if msg.startswith(p):
                return True
        return False

    # source: http://stackoverflow.com/a/32640407/1443726
    def _num_to_words(self, num):
        d = { 0 : 'zero', 1 : 'one', 2 : 'two', 3 : 'three', 4 : 'four', 5 : 'five',
              6 : 'six', 7 : 'seven', 8 : 'eight', 9 : 'nine', 10 : 'ten',
              11 : 'eleven', 12 : 'twelve', 13 : 'thirteen', 14 : 'fourteen',
              15 : 'fifteen', 16 : 'sixteen', 17 : 'seventeen', 18 : 'eighteen',
              19 : 'nineteen', 20 : 'twenty',
              30 : 'thirty', 40 : 'forty', 50 : 'fifty', 60 : 'sixty',
              70 : 'seventy', 80 : 'eighty', 90 : 'ninety' }
        k = 1000
        m = k * 1000
        b = m * 1000
        t = b * 1000

        assert(0 <= num)

        if (num < 20):
            return d[num]

        if (num < 100):
            if num % 10 == 0: return d[num]
            else: return d[num // 10 * 10] + '-' + d[num % 10]

        if (num < k):
            if num % 100 == 0: return d[num // 100] + ' hundred'
            else: return d[num // 100] + ' hundred and ' + int_to_en(num % 100)

        if (num < m):
            if num % k == 0: return int_to_en(num // k) + ' thousand'
            else: return int_to_en(num // k) + ' thousand, ' + int_to_en(num % k)

        if (num < b):
            if (num % m) == 0: return int_to_en(num // m) + ' million'
            else: return int_to_en(num // m) + ' million, ' + int_to_en(num % m)

        if (num < t):
            if (num % b) == 0: return int_to_en(num // b) + ' billion'
            else: return int_to_en(num // b) + ' billion, ' + int_to_en(num % b)

        if (num % t == 0): return int_to_en(num // t) + ' trillion'
        else: return int_to_en(num // t) + ' trillion, ' + int_to_en(num % t)

        raise AssertionError('num is too large: %s' % str(num))

def check_folders():
    folders = ("data", "data/bias/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"YOUR_SERVER_ID": {
        "MAX_ROLES" : 3,
        "ASSIGNABLE_ROLES": {
            "alias": "role"
        },
        "CHANNELS": ["your channel"]
    }
    }

    if not os.path.isfile("data/bias/settings.json"):
        print("Creating empty settings.json...")
        dataIO.save_json("data/bias/settings.json", settings)

def setup(bot):
    check_folders()
    check_files()
    n = Bias(bot)
    bot.add_listener(n.check_message, "on_message")
    bot.add_cog(n)
