import discord
from random import choice as randchoice
from .utils import checks
from discord.ext import commands
import os
from .utils.dataIO import dataIO
import asyncio
import re

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class PrettyCards:
    """Shows pretty cards!"""

    # documentation: https://github.com/Rapptz/discord.py/blob/master/discord/embeds.py

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.mod_or_permissions(administrator=True)
    async def profilecard(self, name : str):
        """Prints a profile card from the specified profile"""

        name = name.strip().lower()

        if re.match(r"^([A-Za-z0-9]+)$", name) == None:
            await self.bot.say("Invalid profile name :warning:")
            return

        f = "data/prettycards/profile-" + name + ".json"
        if not dataIO.is_valid_json(f):
            await self.bot.say("Unable to find profile")
            return

        profile = dataIO.load_json(f)

        try:
            colour = int(profile["colour"], 16)
        except (KeyError, ValueError):
            colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
            colour = int(colour, 16)

        data = discord.Embed(
            description=profile["description"],
            colour=discord.Colour(value=colour))
        data.add_field(name="Groups", value=str(profile["groups"]))
        data.add_field(name="Birthday", value=str(profile["birthday"]))

        data.add_field(name="Position in group", value=str(profile["position_in_group"]))
        data.add_field(name="Birthplace", value=str(profile["birthplace"]))

        data.add_field(name="Company", value=str(profile["company"]))
        data.add_field(name="Blood Type", value=str(profile["bloodtype"]))

        data.add_field(name="Languages", value=str(profile["languages"]))
        data.add_field(name="Weight", value=str(profile["weight"]))

        data.add_field(name="Hobbies", value=str(profile["hobbies"]))
        data.add_field(name="Height", value=str(profile["height"]))

        data.set_author(name=profile["name"], url=profile["picture"])
        data.set_thumbnail(url=profile["picture"])

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command(name="profilecard-replace")
    @checks.mod_or_permissions(administrator=True)
    async def profilecard_replace(self, editChannel : discord.Channel, editMessageId : str, name : str):
        """Prints a profile card from the specified profile"""

        try:
            editMessage = await self.bot.get_message(editChannel, editMessageId)
        except Exception:
            await self.bot.say("Unable to get message :warning:")
            return

        name = name.strip().lower()

        if re.match(r"^([A-Za-z0-9]+)$", name) == None:
            await self.bot.say("Invalid profile name :warning:")
            return

        f = "data/prettycards/profile-" + name + ".json"
        if not dataIO.is_valid_json(f):
            await self.bot.say("Unable to find profile")
            return

        profile = dataIO.load_json(f)

        try:
            colour = int(profile["colour"], 16)
        except (KeyError, ValueError):
            colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
            colour = int(colour, 16)

        data = discord.Embed(
            description=profile["description"],
            colour=discord.Colour(value=colour))
        data.add_field(name="Groups", value=str(profile["groups"]))
        data.add_field(name="Birthday", value=str(profile["birthday"]))

        data.add_field(name="Position in group", value=str(profile["position_in_group"]))
        data.add_field(name="Birthplace", value=str(profile["birthplace"]))

        data.add_field(name="Company", value=str(profile["company"]))
        data.add_field(name="Blood Type", value=str(profile["bloodtype"]))

        data.add_field(name="Languages", value=str(profile["languages"]))
        data.add_field(name="Weight", value=str(profile["weight"]))

        data.add_field(name="Hobbies", value=str(profile["hobbies"]))
        data.add_field(name="Height", value=str(profile["height"]))

        data.set_author(name=profile["name"], url=profile["picture"])
        data.set_thumbnail(url=profile["picture"])

        try:
            await self.bot.edit_message(editMessage, embed=data)
            await self.bot.say("Done :ok_hand:")
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")

    @commands.command(pass_context=True)
    async def videocard(self, ctx, *, arguments : str):
        """Prints a video card from the arguments <title>;description;thumbnail;hoster=link;..."""
        message = ctx.message
        author = message.author

        content = arguments.strip().split(";")

        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        if len(content) <= 2:
            await self.bot.say("Not enough arguments")
            return

        title = content[0]
        content.pop(0)
        description = content[0]
        content.pop(0)
        thumbnail = content[0]
        content.pop(0)

        if len(content) <= 0:
            await self.bot.say("Not enough arguments")
            return

        data = discord.Embed(
            description=str(description),
            colour=discord.Colour(value=colour))
        fallbackText = ""

        for hosterandlink in content:
            if "=" not in hosterandlink:
                continue
            hosterandlink = hosterandlink.split("=")
            if len(hosterandlink) < 2:
                continue
            data.add_field(name=str(hosterandlink[0].strip()), value=str(hosterandlink[1].strip()))
            fallbackText += "`{0}:` <{1}>\n".format(hosterandlink[0].strip(), hosterandlink[1].strip())


        data.set_author(name=str(title))

        if thumbnail != "":
            data.set_thumbnail(url=thumbnail)

        data.set_footer(text="Posted by {}. Thank you!".format(author.name), icon_url=author.avatar_url)

        try:
            await self.bot.say(fallbackText, embed=data)
            #await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

        await asyncio.sleep(10)
        await self.bot.delete_message(message)


def check_folders():
    folders = ("data", "data/prettycards/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def setup(bot):
    check_folders()
    bot.add_cog(PrettyCards(bot))
