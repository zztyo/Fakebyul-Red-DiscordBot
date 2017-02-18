import discord
import os
import aiohttp
import datetime
from .utils import checks
from discord.ext import commands
from __main__ import send_cmd_help
from cogs.utils.dataIO import dataIO


class Lastfm:
    """Le Last.fm cog"""
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = 'data/lastfm/lastfm.json'
        settings = dataIO.load_json(self.settings_file)
        self.api_key = settings['LASTFM_API_KEY']

        self.payload = {}
        self.payload['api_key'] = self.api_key
        self.payload['format'] = 'json'
        self.payload['limit'] = '10'

    @commands.group(pass_context=True, no_pm=True, name='lastfm', aliases=['lf'])
    async def _lastfm(self, context):
        """Get Last.fm statistics of a user.

        Will remember your username after setting one. [p]lastfm last @username will become [p]lastfm last."""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_lastfm.command(pass_context=True, no_pm=True, name='set')
    async def _set(self, context, *username: str):
        """Set a username"""
        if username:
            try:
                payload = self.payload
                payload['method'] = 'user.getInfo'
                payload['username'] = username[0]
                url = 'http://ws.audioscrobbler.com/2.0/?'
                headers = {'user-agent': 'Red-cog/1.0'}
                conn = aiohttp.TCPConnector(verify_ssl=False)
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    data = await r.json()
                session.close()
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = '{}'.format(data['message'])
            else:
                settings = dataIO.load_json(self.settings_file)
                settings['USERS'][context.message.author.id] = username[0]
                username = username[0]
                dataIO.save_json(self.settings_file, settings)
                message = 'Username set'
        else:
            message = 'Now come on, I need your username!'
        await self.bot.say('```{}```'.format(message))

    @_lastfm.command(pass_context=True, no_pm=True, name='info')
    async def _info(self, context, *username: str):
        """Retrieve general information"""
        embedData = None
        message = ""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
                else:
                    await self.bot.say("```Please set your lastfm username with /lf set <username> first```")
                    return
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['method'] = 'user.getInfo'
                payload['username'] = username
                url = 'http://ws.audioscrobbler.com/2.0/?'
                headers = {'user-agent': 'Red-cog/1.0'}
                conn = aiohttp.TCPConnector(verify_ssl=False)
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    data = await r.json()
                session.close()
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = '{}'.format(data['message'])
            else:
                user = data['user']['name']
                playcount = data['user']['playcount']
                registered = data['user']['registered']['unixtime']
                registered = datetime.datetime.fromtimestamp(int(registered))
                profile = data['user']['url']

                days_since = (datetime.datetime.now() - registered).days

                embedData = discord.Embed(
                    title="{0}'s profile".format(user),
                    url=profile,
                    colour=discord.Colour(value=int("B90000", 16)))
                embedData.add_field(name="Scrobbles", value=str(playcount))
                embedData.add_field(name="Registered", value=str("{0}\n({1} days ago)".format(registered.strftime('%Y-%m-%d %H:%M:%S'), days_since)))
                embedData.set_author(name="last.fm", url="https://www.last.fm/")
                #message = 'Last.fm profile of {}\n\nScrobbles: {}\nRegistered: {}\nProfile: {}'.format(user, playcount, registered, profile)
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
        if embedData != None:
            await self.bot.say(embed=embedData)
        else:
            await self.bot.say('```{}```'.format(message))

    @_lastfm.command(pass_context=True, no_pm=True, name='last', aliases=['lp'])
    async def _last(self, context, *username: str):
        """Shows the last 10 played songs"""
        embedData = None
        message = ""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
                else:
                    await self.bot.say("```Please set your lastfm username with /lf set <username> first```")
                    return
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['method'] = 'user.getRecentTracks'
                payload['username'] = username
                url = 'http://ws.audioscrobbler.com/2.0/?'
                headers = {'user-agent': 'Red-cog/1.0'}
                conn = aiohttp.TCPConnector(verify_ssl=False)
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    data = await r.json()
                session.close()
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = '{}'.format(data['message'])
            else:
                user = data['recenttracks']['@attr']['user']

                embedData = discord.Embed(
                    title="{0}\'s last 10 songs played".format(user),
                    url="http://www.last.fm/user/{0}".format(user),
                    colour=discord.Colour(value=int("B90000", 16)))
                embedData.set_author(name="last.fm", url="https://www.last.fm/")
                #message = '```Last 10 songs played by {}\n\n'.format(user)
                for i, track in enumerate(data['recenttracks']['track'], 1):
                    try:
                        if track['@attr']['nowplaying'] == 'true':
                            nowplaying = ':musical_note: '
                    except KeyError:
                        nowplaying = ''
                    print(track['artist'])
                    if '#text' in track['artist']:
                        artist = track['artist']['#text']
                    else:
                        artist = track['artist']['name']
                    song = track['name']
                    embedData.add_field(name="{0}".format(str(i).ljust(4)), value="{2}{0} by {1}".format(song, artist, nowplaying), inline=False)
                    #message += '{} {}{} - {}\n'.format(str(i).ljust(4), nowplaying, artist, song)
                    if i > 9:
                        break
                #message += '```'
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
        if embedData != None:
            await self.bot.say(embed=embedData)
        else:
            await self.bot.say(message)

    @_lastfm.command(pass_context=True, no_pm=True, name='toptracks', aliases=['tracks', 'ttr'])
    async def _toptracks(self, context, *username: str):
        """Top 10 most played songs"""
        embedData = None
        message = ""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
                else:
                    await self.bot.say("```Please set your lastfm username with /lf set <username> first```")
                    return
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['method'] = 'user.getTopTracks'
                payload['username'] = username
                headers = {'user-agent': 'Red-cog/1.0'}
                url = 'http://ws.audioscrobbler.com/2.0/?'
                conn = aiohttp.TCPConnector(verify_ssl=False)
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    data = await r.json()
                session.close()
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = '{}'.format(data['message'])
            else:
                user = data['toptracks']['@attr']['user']
                #message = 'Top songs played by {0}\n\n'.format(user)

                embedData = discord.Embed(
                    title="{0}'s top songs played".format(user),
                    url="http://www.last.fm/user/{0}".format(user),
                    colour=discord.Colour(value=int("B90000", 16)))
                embedData.set_author(name="last.fm", url="https://www.last.fm/")

                for i, track in enumerate(data['toptracks']['track'], 1):
                    artist = track['artist']['name']
                    song = track['name']
                    embedData.add_field(name=str(i).ljust(4), value="{0} by {1}".format(song, artist), inline=False)
                    #message += '{} {} - {}\n'.format(str(i).ljust(4), artist, song)

        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
        if embedData != None:
            await self.bot.say(embed=embedData)
        else:
            await self.bot.say('```{}```'.format(message))

    @_lastfm.command(pass_context=True, no_pm=True, name='topartists', aliases=['artists', 'tar'])
    async def _topartists(self, context, *username: str):
        """Top 10 played artists"""
        embedData = None
        message = ""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
                else:
                    await self.bot.say("```Please set your lastfm username with /lf set <username> first```")
                    return
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['method'] = 'user.getTopArtists'
                payload['username'] = username
                headers = {'user-agent': 'Red-cog/1.0'}
                url = 'http://ws.audioscrobbler.com/2.0/?'
                conn = aiohttp.TCPConnector(verify_ssl=False)
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    data = await r.json()
                session.close()
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)

            if 'error' in data:
                message = '{}'.format(data['message'])
            else:
                user = data['topartists']['@attr']['user']
                #message = 'Top artists played by {}\n\n'.format(user)

                embedData = discord.Embed(
                    title="{0}'s top artists".format(user),
                    url="http://www.last.fm/user/{0}".format(user),
                    colour=discord.Colour(value=int("B90000", 16)))
                embedData.set_author(name="last.fm", url="https://www.last.fm/")
                
                for i, artist in enumerate(data['topartists']['artist'], 1):
                    artist_a = artist['name']
                    embedData.add_field(name=str(i).ljust(4), value=str(artist_a), inline=False)
                    #message += '{} {}\n'.format(str(i).ljust(4), artist_a)

        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
        if embedData != None:
            await self.bot.say(embed=embedData)
        else:
            await self.bot.say('```{}```'.format(message))

    @_lastfm.command(pass_context=True, no_pm=True, name='topalbums', aliases=['albums', 'tab'])
    async def _topalbums(self, context, *username: str):
        """Top 10 played albums"""
        embedData = None
        message = ""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
                else:
                    await self.bot.say("```Please set your lastfm username with /lf set <username> first```")
                    return
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['method'] = 'user.getTopAlbums'
                payload['username'] = username
                headers = {'user-agent': 'Red-cog/1.0'}
                url = 'http://ws.audioscrobbler.com/2.0/?'
                conn = aiohttp.TCPConnector(verify_ssl=False)
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    data = await r.json()
                session.close()
                print(data)
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = '{}'.format(data['message'])
            else:
                user = data['topalbums']['@attr']['user']
                #message = 'Top albums played by {0}\n\n'.format(user)

                embedData = discord.Embed(
                    title="{0}'s top albums".format(user),
                    url="http://www.last.fm/user/{0}".format(user),
                    colour=discord.Colour(value=int("B90000", 16)))
                embedData.set_author(name="last.fm", url="https://www.last.fm/")
                
                for i, album in enumerate(data['topalbums']['album'], 1):
                    albums = album['name']
                    artist = album['artist']['name']
                    #message += '{} {} by {}\n'.format(str(i).ljust(4), albums, artist)
                    embedData.add_field(name=str(i).ljust(4), value="{0} by {1}".format(albums, artist), inline=False)
        else:
            message = 'No API key set. Get one at http://www.last.fm/api'
        if embedData != None:
            await self.bot.say(embed=embedData)
        else:
            await self.bot.say('```{}```'.format(message))

    @_lastfm.command(pass_context=True, no_pm=True, name='np')
    async def _np(self, context, *username: str):
        """Shows what you are currently playing"""
        embedData = None
        message = ""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
                else:
                    await self.bot.say("```Please set your lastfm username with /lf set <username> first```")
                    return
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['method'] = 'user.getRecentTracks'
                payload['username'] = username
                payload['limit'] = 1
                payload['extended'] = 1
                url = 'http://ws.audioscrobbler.com/2.0/?'
                headers = {'user-agent': 'Red-cog/1.0'}
                conn = aiohttp.TCPConnector(verify_ssl=False)
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    data = await r.json()
                session.close()
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = '{}'.format(data['message'])
            else:
                user = data['recenttracks']['@attr']['user']
                track = data['recenttracks']['track']
                message = ''
                try:
                    #artist = track[0]['artist']['#text']
                    artist = track[0]['artist']['name']
                    song = track[0]['name']
                    url = track[0]['url']
                    image = ""
                    for imageSource in track[0]['image']:
                        if imageSource['size'] == 'large':
                            image = imageSource['#text']
                            break

                    try:
                        if track[0]['@attr']['nowplaying'] == 'true':
                            #message = '**{}** is currently listening to **{}** by **{}**'.format(context.message.author.name, song, artist)
                            embedData = discord.Embed(
                                title="{2} is currently listening to {0} by {1}".format(song, artist, user),
                                url=url,
                                colour=discord.Colour(value=int("B90000", 16)))
                    except KeyError:
                    #    message = ''
                        embedData = discord.Embed(
                            title="{2} last listened to {0} by {1}".format(song, artist, user),
                            url=url,
                            colour=discord.Colour(value=int("B90000", 16)))
                    #if message == '':
                    #    message = '**{}** last listened to **{}** by **{}**'.format(context.message.author.name, song, artist)
                    embedData.set_author(name="last.fm", url="https://www.last.fm/")
                    embedData.set_thumbnail(url=image)
                except KeyError:
                    message = 'unable to get recent tracks of {}'.format(user)
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
        if embedData != None:
            await self.bot.say(embed=embedData)
        else:
            await self.bot.say(message)


    @_lastfm.command(pass_context=True, name='apikey')
    @checks.is_owner()
    async def _apikey(self, context, *key: str):
        """Sets the Last.fm API key - for bot owner only."""
        settings = dataIO.load_json(self.settings_file)
        if key:
            settings['LASTFM_API_KEY'] = key[0]
            self.api_key = key[0]
            dataIO.save_json(self.settings_file, settings)
            await self.bot.say('```Done```')


def check_folder():
    if not os.path.exists("data/lastfm"):
        print("Creating data/lastfm folder...")
        os.makedirs("data/lastfm")


def check_file():
    data = {}
    data['LASTFM_API_KEY'] = ''
    data['USERS'] = {}
    f = "data/lastfm/lastfm.json"
    if not dataIO.is_valid_json(f):
        print("Creating default lastfm.json...")
        dataIO.save_json(f, data)


def setup(bot):
    check_folder()
    check_file()
    n = Lastfm(bot)
    bot.add_cog(n)
