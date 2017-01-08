import discord
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
from apiclient.discovery import build
import random
import io
from apiclient.http import MediaIoBaseDownload

class RandomPictures:
    """My custom cog that does RandomPictures!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, name="rapi")
    async def _randompictures(self, context):
        """This does stuff!"""
        channel = context.message.channel

        scopes = ['https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'data/randompictures/Robyul-Red-DiscordBot-334d9f339458.json', scopes=scopes)

        from httplib2 import Http

        http_auth = credentials.authorize(Http())
        service = build('drive', 'v3', http=http_auth)
        folder_ids = ["0BwVumX-VvI_SaU1taDlXZmhZXzQ", "0BwVumX-VvI_SVktfVzM1ZFV6bE0"]
        folder_ids = ["0BwVumX-VvI_SVktfVzM1ZFV6bE0"]
        #folders_search_string = ""
        #i = 0
        #for folder_id in folder_ids:
        #    folders_search_string += '("{0}" in parents)'.format(folder_id)
        #    i += 1
        #    if i < len(folder_ids):
        #        folders_search_string += " or "

        all_files = []
        for folder_id in folder_ids:
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

                all_files.extend(files['files'])
                page_token = files.get('nextPageToken')
                if not page_token:
                    break
            #response = service.files().list(q=search_string).execute()
            #import pprint; pprint.pprint(response)
            #if "files" in response and len(response["files"]) > 0:
            #    all_files += response["files"]

        if len(all_files) <= 0:
            print("No files found!")
            return

        print("Found", len(all_files), "files")
        random_choice = random.choice(all_files)
        import pprint; pprint.pprint(random_choice)

        request = service.files().get_media(fileId=random_choice["id"])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = await downloader.next_chunk()
        await self.bot.send_file(channel, fh, filename=random_choice["name"])
        fh.close()

def setup(bot):
    n = RandomPictures(bot)
    bot.add_cog(n)