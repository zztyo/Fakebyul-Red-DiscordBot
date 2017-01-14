import discord
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
import random
import io
import aiohttp
from __main__ import send_cmd_help
from .utils.chat_formatting import pagify
import datetime
from .utils import checks
import asyncio

__author__ = "Sebastian Winkler"
__version__ = "0.1"

class RandomPictures:
    """My custom cog that does RandomPictures!"""

    def __init__(self, bot, sleep):
        self.bot = bot
        self.sleep = sleep
        self.google_credentials_json = "data/randompictures/google_credentials.json"
        self.picture_download_base_url = "https://www.googleapis.com/drive/v3/files/{0}?alt=media"
        self.database = [
        {"folder_ids": ["0BwVumX-VvI_SaU1taDlXZmhZXzQ"], "label": "임나영"}, #Nayoung
        {"folder_ids": ["0BwVumX-VvI_SaUQ2WW9NUkQ0bnc",
        "0BwVumX-VvI_SZERaVXFPRUJWQWM",
        "0BwVumX-VvI_SVktfVzM1ZFV6bE0",
        "0BwVumX-VvI_SWEZQMXNRc2phaFk",
        "0BwVumX-VvI_SM3J0SWhJdzVLY28",
        "0BwVumX-VvI_SS2Y2NVB2V292R3c",
        "0BwVumX-VvI_SVG5HeEgzQ1lHNnc",
        "0BwVumX-VvI_SQnpBU1NqbEcyLVk",
        "0BwVumX-VvI_SSWdETXpCUTJNclk",
        "0BwVumX-VvI_SNzNpTGtCYXVsU1E",
        "0BwVumX-VvI_SMVNCTWZoaEpRZVk",
        "0BwVumX-VvI_SaU1taDlXZmhZXzQ"],
        #"post_to_channels": ["253541413948489728"],
        "label": "아이오아이"}
        ]
        self.settings = {"post_interval": 60}
        self.picture_database = {}
        self.refresh_in_progress = False

    @commands.group(pass_context=True, no_pm=True, name="randompictures", aliases=["rapi"])
    async def _randompictures(self, context):
        """Manages RandomPictures entries"""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_randompictures.command(pass_context=True, no_pm=True, name="stats")
    async def _randompictures_stats(self, context):
        """Lists google drive pictures in the cache"""
        if len(self.database) <= 0:
            await self.bot.say("No entries in the DB!")
            return

        message = ""
        for entry in self.database:
            num = self.database.index(entry)
            total_pictures = 0
            last_pictures_cache_refresh = "Never"
            label = ""
            if num in self.picture_database:
                if "last_pictures_cache_refresh" in self.picture_database[num]:
                    last_pictures_cache_refresh = self.picture_database[num]["last_pictures_cache_refresh"].strftime("%Y-%m-%d %H:%M UTC")
                if "pictures_cache" in self.picture_database[num]:
                    total_pictures = len(self.picture_database[num]["pictures_cache"])
            if "label" in entry and entry["label"] != "":
                label = " (**{0}**) ".format(entry["label"])

            message += "`#{0}`{4}: `{2}` pictures in cache, last refresh: `{3}`, folder(s):\n".format(num, entry, total_pictures, last_pictures_cache_refresh, label)
            for folder_id in entry["folder_ids"]:
                message += "<https://drive.google.com/drive/folders/{0}>\n".format(folder_id)
            if "post_to_channels" in entry and entry["post_to_channels"] != "" and len(entry["post_to_channels"]) > 0:
                message += "posting to:\n"
                for channel_id in entry["post_to_channels"]:
                    channel = self.bot.get_channel(channel_id)
                    if channel != None:
                        message += "{0.server.name}/{0.mention}\n".format(channel)
                    else:
                        message += "`#{0}` (channel not found!)\n".format(channel_id)

        for page in pagify(message, delims=["\n"]):
            await self.bot.say(page)

    @_randompictures.command(pass_context=True, no_pm=True, name="refresh")
    @checks.mod_or_permissions(administrator=True)
    async def _randompictures_refresh(self, context, num: int):
        """Refreshes the picture DB from the google drive folder(s)"""

        self.picture_database[num] = {"pictures_cache": []}
        for folder_id in self.database[num]["folder_ids"]:
            await self._refresh_cache_num(num, folder_id)

        await self.bot.say("Found {0} pictures!".format(len(self.picture_database[num]["pictures_cache"])))

    @_randompictures.command(pass_context=True, no_pm=True, name="force")
    async def _randompictures_force(self, context, num: int):
        """Posts a random picture from the specified folders"""
        channel = context.message.channel

        if len(self.database) < num+1:
            await self.bot.say("Entry not found in database")
            return

        if num not in self.picture_database:
            self.picture_database[num] = {"pictures_cache": []}
        elif "pictures_cache" not in self.picture_database[num]:
            self.picture_database[num] = {"pictures_cache": []}

        if len(self.picture_database[num]["pictures_cache"]) <= 0:
            await self.bot.say("Refreshing database...")
            if self.refresh_in_progress == False:
                await self._randompictures_refresh.callback(self=self, context=context, num=num)
            else:
                await self.bot.say("Refreshing already in progress!")
                return

        if len(self.picture_database[num]["pictures_cache"]) <= 0:
            await self.bot.say("No pictures found in this entry")
            return

        await self._post_random_picture(num, channel)

    def _get_credentials(self):
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.google_credentials_json, scopes=scopes)
        return credentials

    async def _post_random_picture(self, num, channel):
        while True:
            random_choice = random.choice(self.picture_database[num]["pictures_cache"])
            if not "size" in random_choice or random_choice["size"] == "" or int(random_choice["size"]) >= 8e+6: # discord 8 mb file limit
                continue
            break

        random_picture_download_url = self.picture_download_base_url.format(random_choice["id"])

        credentials = self._get_credentials()

        conn = aiohttp.TCPConnector(verify_ssl=False)
        with aiohttp.ClientSession(connector=conn) as session:
            headers = {"user-agent": "Red-cog-RandomPictures/"+__version__, "Authorization": "Bearer {0.access_token}".format(credentials.get_access_token())}

            async with await session.get(random_picture_download_url, headers=headers) as resp:
                image = await resp.read()

                with io.BytesIO(image) as file_obj:
                    await self.bot.send_file(channel, file_obj, filename=random_choice["name"])

    async def _refresh_cache_num(self, num, folder_id):
        self.refresh_in_progress = True
        conn = aiohttp.TCPConnector(verify_ssl=False)
        with aiohttp.ClientSession(connector=conn) as session:
            credentials = self._get_credentials()
            headers = {"user-agent": "Red-cog-RandomPictures/"+__version__, "Authorization": "Bearer {0.access_token}".format(credentials.get_access_token())}
            url = "https://www.googleapis.com/drive/v3/files"
            search_string = '"{0}" in parents and (mimeType = "image/gif" or mimeType = "image/jpeg" or mimeType = "image/png")'.format(folder_id)
            page_token = None
            while True:
                print("Executing:", search_string, ", page_token:", page_token)
                param = {}
                if page_token:
                    param['pageToken'] = page_token
                param['q'] = search_string
                param['fields'] = 'nextPageToken, files(id, name, size)'
                param['pageSize'] = 1000

                async with session.get(url, params=param, headers=headers) as r:
                    files = await r.json()

                    self.picture_database[num]["pictures_cache"].extend(files['files'])
                    page_token = files.get('nextPageToken')
                    if not page_token:
                        break
        self.picture_database[num]["last_pictures_cache_refresh"] = datetime.datetime.utcnow()
        self.refresh_in_progress = False

    async def refresh_cache_loop(self, sleep, loop):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('RandomPictures'):
            print("[RandomPictures] refreshing picture caches...")
            for entry in self.database:
                num = self.database.index(entry)
                self.picture_database[num] = {"pictures_cache": []}
                for folder_id in self.database[num]["folder_ids"]:
                    if self.refresh_in_progress == False:
                        try:
                            print("[RandomPictures] refreshing picture cache (#{0}/{1})...".format(num, folder_id))
                            await self._refresh_cache_num(num, folder_id)
                        except Exception as e:
                            print("[RandomPictures] refreshing picture cache (#{0}/{1}) failed:".format(num, folder_id), e)
                    else:
                        print("[RandomPictures] refreshing picture cache (#{0}/{1}) failed:".format(num, folder_id), "refresh already in progress!")
            await loop.create_task(sleep(86400)) # one day

    async def post_pictures_loop(self, sleep, loop):
        await self.bot.wait_until_ready()
        if "post_interval" in self.settings and self.settings["post_interval"] != "":
            while self == self.bot.get_cog('RandomPictures'):
                await loop.create_task(sleep(int(self.settings["post_interval"]))) # sleep first (because of initial refresh)
                print("[RandomPictures] posting random pictures...")
                for entry in self.database:
                    num = self.database.index(entry)
                    if "post_to_channels" in entry and entry["post_to_channels"] != "" and len(entry["post_to_channels"]) > 0:
                        for channel_id in entry["post_to_channels"]:
                            channel = self.bot.get_channel(channel_id)
                            if channel != None:
                                await self._post_random_picture(num, channel)

def make_sleep():
    async def sleep(delay, result=None, *, loop=None):
        coro = asyncio.sleep(delay, result=result, loop=loop)
        task = asyncio.ensure_future(coro)
        sleep.tasks.add(task)
        try:
            return await task
        except asyncio.CancelledError:
            return result
        finally:
            sleep.tasks.remove(task)

    sleep.tasks = set()
    sleep.cancel_all = lambda: sum(task.cancel() for task in sleep.tasks)
    return sleep

def setup(bot):
    sleep = make_sleep()
    loop = asyncio.get_event_loop()
    n = RandomPictures(bot, sleep)
    bot.add_cog(n)
    bot.loop.create_task(n.refresh_cache_loop(sleep, loop))
    bot.loop.create_task(n.post_pictures_loop(sleep, loop))