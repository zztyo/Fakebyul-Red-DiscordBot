import discord
from random import choice as randchoice
from .utils import checks
from discord.ext import commands
import os
from .utils.dataIO import dataIO

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class PrettyCards:
    """Shows pretty cards!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.mod_or_permissions(administrator=True)
    async def profilecard(self, name : str):
        """Prints a profile card from the specified profile"""

        name = name.strip().lower()

        f = "data/prettycards/profile-" + name + ".json"
        if not dataIO.is_valid_json(f):
            await self.bot.say("Unable to find profile")
            return

        profile = dataIO.load_json(f)

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

        #data.set_footer(icon_url=profile["picture"])

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")


def check_folders():
    folders = ("data", "data/prettycards/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def setup(bot):
    check_folders()
    bot.add_cog(PrettyCards(bot))
