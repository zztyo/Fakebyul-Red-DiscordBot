import discord
from random import choice as randchoice
from .utils import checks
from discord.ext import commands
import os
from .utils.dataIO import dataIO
import asyncio
import re
import aiohttp
import json
import copy
from datetime import datetime

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "1.1"

class PrettyCards:
    """Shows pretty cards!"""

    # documentation: https://github.com/Rapptz/discord.py/blob/master/discord/embeds.py

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/prettycards/settings.json"
        self.settings = dataIO.load_json(self.file_path)
        self.countdowns_file_path = "data/prettycards/countdowns.json"
        self.countdowns = dataIO.load_json(self.countdowns_file_path)

    @commands.command()
    @checks.mod_or_permissions(administrator=True)
    async def profilecard(self, name : str):
        """Prints a profile card from the specified profile"""

        name = name.strip().lower()

        if re.match(r"^([A-Za-z0-9\-]+)$", name) == None:
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
        if "groups" in profile and profile["groups"] != "":
            data.add_field(name="Groups", value=str(profile["groups"]))
        data.add_field(name="Birthday", value=str(profile["birthday"]))

        data.add_field(name="Position in group", value=str(profile["position_in_group"]))
        data.add_field(name="Birthplace", value=str(profile["birthplace"]))

        if "company" in profile and profile["company"] != "":
            data.add_field(name="Company", value=str(profile["company"]))
        data.add_field(name="Blood Type", value=str(profile["bloodtype"]))

        data.add_field(name="Languages", value=str(profile["languages"]))
        data.add_field(name="Weight", value=str(profile["weight"]))

        data.add_field(name="Hobbies", value=str(profile["hobbies"]))
        data.add_field(name="Height", value=str(profile["height"]))

        if "skills" in profile and profile["skills"] != "":
            data.add_field(name="Skills", value=str(profile["skills"]))
        if "training" in profile and profile["training"] != "":
            data.add_field(name="Training time", value=str(profile["training"]))
        if "education" in profile and profile["education"] != "":
            data.add_field(name="Education", value=str(profile["education"]))
        if "strengths" in profile and profile["strengths"] != "":
            data.add_field(name="Strengths", value=str(profile["strengths"]), inline=False)
        if "weaknesses" in profile and profile["weaknesses"] != "":
            data.add_field(name="Weaknesses", value=str(profile["weaknesses"]), inline=False)

        if "future" in profile and profile["future"] != "":
            data.add_field(name="Future plans", value=str(profile["future"]), inline=False)

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

        if re.match(r"^([A-Za-z0-9\-]+)$", name) == None:
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
        if "groups" in profile and profile["groups"] != "":
            data.add_field(name="Groups", value=str(profile["groups"]))
        data.add_field(name="Birthday", value=str(profile["birthday"]))

        data.add_field(name="Position in group", value=str(profile["position_in_group"]))
        data.add_field(name="Birthplace", value=str(profile["birthplace"]))

        if "company" in profile and profile["company"] != "":
            data.add_field(name="Company", value=str(profile["company"]))
        data.add_field(name="Blood Type", value=str(profile["bloodtype"]))

        data.add_field(name="Languages", value=str(profile["languages"]))
        data.add_field(name="Weight", value=str(profile["weight"]))

        data.add_field(name="Hobbies", value=str(profile["hobbies"]))
        data.add_field(name="Height", value=str(profile["height"]))

        if "skills" in profile and profile["skills"] != "":
            data.add_field(name="Skills", value=str(profile["skills"]))
        if "training" in profile and profile["training"] != "":
            data.add_field(name="Training time", value=str(profile["training"]))
        if "education" in profile and profile["education"] != "":
            data.add_field(name="Education", value=str(profile["education"]))
        if "strengths" in profile and profile["strengths"] != "":
            data.add_field(name="Strengths", value=str(profile["strengths"]), inline=False)
        if "weaknesses" in profile and profile["weaknesses"] != "":
            data.add_field(name="Weaknesses", value=str(profile["weaknesses"]), inline=False)

        if "future" in profile and profile["future"] != "":
            data.add_field(name="Future plans", value=str(profile["future"]), inline=False)
            
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
            hosterandlink = hosterandlink.split("=", 1)
            if len(hosterandlink) < 2:
                continue
            shortenedLink = await self._shorten_url_googl(str(hosterandlink[1].strip()))
            data.add_field(name=str(hosterandlink[0].strip()), value=shortenedLink)
            fallbackText += "`{0}:` <{1}>\n".format(hosterandlink[0].strip(), shortenedLink)


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


    @commands.command(pass_context=True, name="videocard-replace")
    @checks.mod_or_permissions(administrator=True)
    async def videocard_replace(self, ctx, editChannel : discord.Channel, editMessageId : str, *, arguments : str):
        """Prints a video card from the arguments <title>;description;thumbnail;hoster=link;..."""

        try:
            editMessage = await self.bot.get_message(editChannel, editMessageId)
        except Exception:
            await self.bot.say("Unable to get message :warning:")
            return

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
            hosterandlink = hosterandlink.split("=", 1)
            if len(hosterandlink) < 2:
                continue
            shortenedLink = await self._shorten_url_googl(str(hosterandlink[1].strip()))
            data.add_field(name=str(hosterandlink[0].strip()), value=shortenedLink)
            fallbackText += "`{0}:` <{1}>\n".format(hosterandlink[0].strip(), shortenedLink)


        data.set_author(name=str(title))

        if thumbnail != "":
            data.set_thumbnail(url=thumbnail)

        data.set_footer(text="Posted by {}. Thank you!".format(author.name), icon_url=author.avatar_url)

        try:
            await self.bot.edit_message(editMessage, fallbackText, embed=data)
            await self.bot.say("Done :ok_hand:")
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

    @commands.group(pass_context=True, no_pm=True, name="countdown")
    @checks.mod_or_permissions(administrator=True)
    async def _countdown(self, ctx):
        """Creates countdown cards"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_countdown.command(pass_context=True, name="until")
    @checks.mod_or_permissions(administrator=True)
    async def _countdown_until(self, ctx, datetime_str : str, description : str, finished_message=""):
        """Creates a countdown until date, YYYY-MM-DD HH:MM (24 hour clock, UTC)"""
        message = ctx.message
        author = message.author
        description = description.strip()
        finished_message = finished_message.strip()
        try:
            datetime_countdown = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            await self.bot.say("Invalid date!")
            return
        datetime_now = datetime.utcnow()
        if datetime_now > datetime_countdown:
            await self.bot.say("You gave me a date from the past... :thinking:")
            return

        data = self._get_countdown_embed(datetime_countdown, description)

        countdown_number = str(len(self.countdowns)+1)
        while True:
            if countdown_number in self.countdowns:
                countdown_number = str(int(countdown_number)+1)
            else:
                break
        countdown_message = await self.bot.say(embed=data)

        self.countdowns[countdown_number] = {"messageId": countdown_message.id, "type": "until", "createdBy": author.id, "channelId": countdown_message.channel.id, "description": description, "datetime": datetime_countdown.strftime("%Y-%m-%d %H:%M"), "finishedMessage": finished_message}
        dataIO.save_json(self.countdowns_file_path, self.countdowns)

    def _get_countdown_embed(self, datetime_countdown, description):
        datetime_now = datetime.utcnow()

        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        data = discord.Embed(
            description=str(description),
            colour=discord.Colour(value=colour))
        data.set_author(name=str("Countdown"))
        data.set_footer(text="countdown until: {0} UTC, last updated: {1} UTC".format(datetime_countdown.strftime("%Y-%m-%d %H:%M"), datetime_now.strftime("%Y-%m-%d %H:%M")))

        if datetime_now > datetime_countdown:
            data.set_author(name=str("Countdown over!"))
        else:
            datetime_delta = datetime_countdown - datetime_now
            delta_seconds = datetime_delta.total_seconds()
            delta_hours = int((delta_seconds-(datetime_delta.days*24*3600)) // 3600)
            delta_minutes = int((delta_seconds % 3600) // 60)

            data.add_field(name="Days left", value=datetime_delta.days)
            data.add_field(name="Hours left", value=delta_hours)
            data.add_field(name="Minutes left", value=delta_minutes)
        return data

    async def update_countdowns(self):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('PrettyCards'):
            countdown_cache = copy.deepcopy(self.countdowns)
            for key in countdown_cache:
                countdown = countdown_cache[key]
                countdown_channel = self.bot.get_channel(countdown["channelId"])
                if countdown_channel == None:
                    print("Updating countdown failed: message #{0}, channel not found".format(countdown["messageId"]))
                    del self.countdowns[str(key)]
                    dataIO.save_json(self.countdowns_file_path, self.countdowns)
                    print("Deleted countdown (channel not found): message #{0}".format(countdown["messageId"]))
                    continue
                try:
                    countdown_message = await self.bot.get_message(countdown_channel, countdown["messageId"])
                except discord.NotFound:
                    print("Updating countdown failed: message #{0} not found".format(countdown["messageId"]))
                    del self.countdowns[str(key)]
                    dataIO.save_json(self.countdowns_file_path, self.countdowns)
                    print("Deleted countdown (message not found): message #{0}".format(countdown["messageId"]))
                    continue
                try:
                    datetime_countdown = datetime.strptime(countdown["datetime"], "%Y-%m-%d %H:%M")
                    datetime_now = datetime.utcnow()
                    data = self._get_countdown_embed(datetime_countdown, countdown["description"])
                    countdown_message = await self.bot.edit_message(countdown_message, embed=data)
                    #print("Updated countdown: message #{0.id}".format(countdown_message))
                    if datetime_now > datetime_countdown:
                        del self.countdowns[str(key)]
                        dataIO.save_json(self.countdowns_file_path, self.countdowns)
                        print("Deleted countdown (time is over): message #{0.id}".format(countdown_message))
                        if "finishedMessage" in countdown and countdown["finishedMessage"] != "":
                            await self.bot.send_message(countdown_channel, countdown["finishedMessage"])
                except Exception as e:
                    print("Updating countdown failed: message #{0}, error: {1}".format(countdown["messageId"], e))
            del countdown_cache
            await asyncio.sleep(300)

    async def _shorten_url_googl(self, longUrl):
        if "GOOGL_URL_SHORTENER_API_KEY" not in self.settings or self.settings["GOOGL_URL_SHORTENER_API_KEY"] == "":
            return longUrl

        url = "https://www.googleapis.com/urlshortener/v1/url?key={0}".format(self.settings["GOOGL_URL_SHORTENER_API_KEY"])

        payload = {"longUrl": longUrl}
        headers = {"user-agent": "Red-cog-Prettycards/"+__version__, "content-type": "application/json"}
        try:
            conn = aiohttp.TCPConnector()
            session = aiohttp.ClientSession(connector=conn)
            async with session.post(url, data=json.dumps(payload), headers=headers) as r:
                result = await r.json()
            session.close()
            return result["id"]
        except Exception as e:
            print("Shortening url failed: {0}".format(e))
            return longUrl


def check_folders():
    folders = ("data", "data/prettycards/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"GOOGL_URL_SHORTENER_API_KEY": ""}
    countdowns = {}

    if not os.path.isfile("data/prettycards/settings.json"):
        print("Creating empty settings.json...")
        dataIO.save_json("data/prettycards/settings.json", settings)

    f = "data/prettycards/countdowns.json"
    if not dataIO.is_valid_json(f):
        print("Creating default prettycards countdowns.json...")
        dataIO.save_json(f, countdowns)


def setup(bot):
    check_folders()
    check_files()
    n = PrettyCards(bot)
    bot.loop.create_task(n.update_countdowns())
    bot.add_cog(n)

