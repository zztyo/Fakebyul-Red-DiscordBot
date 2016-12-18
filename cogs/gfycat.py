import discord
from discord.ext import commands
from __main__ import send_cmd_help
from .utils.dataIO import dataIO
import asyncio
import os
import aiohttp
import json

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

# /gfy crt https://www.instagram.com/p/BOG7-gfg_O2/?taken-by=s_sohye
class Gfycat:
    """gfycat cog"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/gfycat/settings.json"
        self.settings = dataIO.load_json(self.file_path)
        self.api_url = "https://api.gfycat.com/v1"
        self.base_url = "https://gfycat.com/{0}"

    @commands.group(pass_context=True, name="gfycat", aliases=["gfy"])
    async def _gfycat(self, ctx):
        """Does gfycat stuff"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_gfycat.command(pass_context=True, name="create", aliases=["crt"])
    async def _create(self, ctx, url : str):
        """Creates a gfycat from a url"""
        author = ctx.message.author

        if url == "":
            await send_cmd_help(ctx)
            return

        await self.bot.say("Talking to gfycat.com, this may take a while... :telephone:")

        result = await self._create_gfycat(url)
        if result == "":
            await self.bot.say("{0.mention} Something went wrong, please try again later! :warning:".format(author))
            return

        gfycatUrl = self.base_url.format(result)
        await self.bot.say("{0.mention} Your gfycat is ready: {1} :sparkles:".format(author, gfycatUrl))

        """
        statusMessage = await self.bot.say("Talking to gfycat.com, this may take a while... :telephone:")
        upload = await GfycatApi.GfycatApi().upload(url)

        if "gfyName" not in upload:
            await self.bot.say("{0.mention} Something went wrong, please try again later! :warning:".format(author))
            print("gfycat error:", upload)
            return

        gfycatUrl = "https://gfycat.com/{0}".format(upload["gfyName"])
        await self.bot.say("{0.mention} Your gfycat: {1}".format(author, gfycatUrl))
        """

    async def _create_gfycat(self, fetchUrl):
        accessToken = await self._get_access_token()
        payload = {"fetchUrl": fetchUrl, "private": True}
        url = self.api_url + "/gfycats"
        headers = {"user-agent": "Red-cog-Gfycat/"+__version__,
                    "content-type": "application/json",
                    "Authorization": accessToken}
        conn = aiohttp.TCPConnector()
        session = aiohttp.ClientSession(connector=conn)
        try:
            async with session.post(url, data=json.dumps(payload), headers=headers) as r:
                result = await r.json()
        except Exception as e:
            print("gfycat getting access token failed: {0}".format(e))
            session.close()
            return ""
        if result["isOk"] != True:
            print("gfycat error:", result)
            session.close()
            return ""
        url = self.api_url + "/gfycats/fetch/status/" + result["gfyname"]
        while True:
            try:
                async with session.get(url, headers=headers) as r:
                    result = await r.json()
            except Exception as e:
                print("gfycat getting gfy status failed: {0}".format(e))
                session.close()
                return ""
            if result["task"] == "encoding":
                await asyncio.sleep(10)
                continue
            if result["task"] == "complete":
                session.close()
                return result["gfyname"]
            else:
                session.close()
                print("gfycat getting gfy status failed:", result)
                return ""

    async def _get_access_token(self):
        payload = {"grant_type": "client_credentials",
                    "client_id": self.settings["GFYCAT_CLIENT_ID"],
                    "client_secret": self.settings["GFYCAT_CLIENT_SECRET"]}
        url = self.api_url + "/oauth/token"
        headers = {"user-agent": "Red-cog-Gfycat/"+__version__,
                    "content-type": "application/json"}
        try:
            conn = aiohttp.TCPConnector()
            session = aiohttp.ClientSession(connector=conn)
            async with session.post(url, data=json.dumps(payload), headers=headers) as r:
                result = await r.json()
            session.close()
            return result["token_type"].capitalize() + " " + result["access_token"]
        except Exception as e:
            print("Getting access token failed: {0}".format(e))
            return ""


def check_folders():
    folders = ("data", "data/gfycat/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    settings = {"GFYCAT_CLIENT_ID": "", "GFYCAT_CLIENT_SECRET": ""}
    if not os.path.isfile("data/gfycat/settings.json"):
        print("Creating empty settings.json, please fill in details...")
        dataIO.save_json("data/gfycat/settings.json", settings)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Gfycat(bot))
