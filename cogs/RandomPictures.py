import discord
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
from apiclient.discovery import build
import random
import io
import aiohttp
from __main__ import send_cmd_help
from .utils.chat_formatting import pagify
import datetime

__author__ = "Sebastian Winkler"
__version__ = "0.1"

class RandomPictures:
    """My custom cog that does RandomPictures!"""

    def __init__(self, bot):
        self.bot = bot
        self.google_credentials_json = "data/randompictures/google_credentials.json"
        self.picture_download_base_url = "https://www.googleapis.com/drive/v3/files/{0}?alt=media"
        self.database = [{"folder_ids": ["0BwVumX-VvI_SaU1taDlXZmhZXzQ"]}]
        self.picture_database = {}

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
            if num in self.picture_database:
                if "last_pictures_cache_refresh" in self.picture_database[num]:
                    last_pictures_cache_refresh = self.picture_database[num]["last_pictures_cache_refresh"].strftime("%Y-%m-%d %H:%M UTC")
                if "pictures_cache" in self.picture_database[num]:
                    total_pictures = len(self.picture_database[num]["pictures_cache"])

            message += "`#{0}`: `{2}` pictures in cache, last refresh: `{3}`, folder(s):\n".format(num, entry, total_pictures, last_pictures_cache_refresh)
            for folder_id in entry["folder_ids"]:
                message += "<https://drive.google.com/drive/folders/{0}>\n".format(folder_id)

        for page in pagify(message, delims=["\n"]):
            await self.bot.say(page)

    @_randompictures.command(pass_context=True, no_pm=True, name="refresh")
    async def _randompictures_refresh(self, context, num: int):
        """Refreshes the picture DB from the google drive folder(s)"""
        # TODO: Way to refresh all
        self.picture_database[num] = {"pictures_cache": []}

        credentials = self._get_credentials()
        http_auth = credentials.authorize(Http())
        service = build('drive', 'v3', http=http_auth)

        for folder_id in self.database[num]["folder_ids"]:
            search_string = '"{0}" in parents and (mimeType = "image/gif" or mimeType = "image/jpeg" or mimeType = "image/png")'.format(folder_id)
            page_token = None
            while True:
                print("Exectuing:", search_string, ", page_token:", page_token)
                param = {}
                if page_token:
                    param['pageToken'] = page_token
                param['q'] = search_string
                param['fields'] = 'nextPageToken, files(id, name)'
                param['pageSize'] = 1000
                files = service.files().list(**param).execute()

                self.picture_database[num]["pictures_cache"].extend(files['files'])
                page_token = files.get('nextPageToken')
                if not page_token:
                    break

        self.picture_database[num]["last_pictures_cache_refresh"] = datetime.datetime.utcnow()
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
            await self._randompictures_refresh.callback(self=self, context=context, num=num)

        if len(self.picture_database[num]["pictures_cache"]) <= 0:
            await self.bot.say("No pictures found in this entry")
            return

        random_choice = random.choice(self.picture_database[num]["pictures_cache"])

        random_picture_download_url = self.picture_download_base_url.format(random_choice["id"])

        credentials = self._get_credentials()

        conn = aiohttp.TCPConnector(verify_ssl=False)
        with aiohttp.ClientSession(connector=conn) as session:
            headers = {"user-agent": "Red-cog-RandomPictures/"+__version__, "Authorization": "Bearer {0.access_token}".format(credentials.get_access_token())}

            async with await session.get(random_picture_download_url, headers=headers) as resp:
                image = await resp.read()

                with io.BytesIO(image) as file_obj:
                    await self.bot.send_file(channel, file_obj, filename=random_choice["name"])

    def _get_credentials(self):
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.google_credentials_json, scopes=scopes)
        return credentials
    
def setup(bot):
    n = RandomPictures(bot)
    bot.add_cog(n)