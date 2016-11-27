import discord
from discord.ext import commands
from random import choice as randchoice
from .utils import kpopcharts
import datetime
from __main__ import send_cmd_help

class Charts:
    """Get charts from various sources!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def charts(self, context):
        """Prints the current charts."""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @charts.group(pass_context=True)
    async def ichart(self, context):
        """Prints ichart charts."""
        if str(context.invoked_subcommand) == "charts ichart":
            await send_cmd_help(context)

    @ichart.command(name="realtime")
    async def realtime_ichart(self):
        """Get the iChart realtime charts!"""
        
        await self.bot.type()

        colour = int("D6D6D6", 16)

        data = discord.Embed(
            title="iChart Realtime Charts",
            url="http://www.instiz.net/iframe_ichart_score.htm?real=1",
            colour=discord.Colour(value=colour))

        charts = list()
        charts.append(kpopcharts.IChart(kpopcharts.ChartType.Realtime))
        normalized = kpopcharts.NormalizedChartList(*charts)

        for entry in normalized[0][:10]:
            if entry.change == "up":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↑{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            elif entry.change == "down":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↓{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            else:
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1}'.format(str(entry.artists), entry.title)), inline=False)

        if normalized[0][0].video != "":
            videoId = normalized[0][0].video.split("/")
            videoId = videoId[len(videoId)-1]
            data.set_thumbnail(url="https://img.youtube.com/vi/{}/hqdefault.jpg".format(videoId))

        data.set_footer(text="Time: {0} UTC".format(str(datetime.datetime.utcnow()).split('.', 1)[0].rsplit(':', 1)[0]))

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

    @ichart.command(name="week")
    async def week_ichart(self):
        """Get the iChart Week charts!"""
        
        await self.bot.type()

        colour = int("D6D6D6", 16)

        data = discord.Embed(
            title="iChart Week Charts",
            url="http://www.instiz.net/iframe_ichart_score.htm?week=1",
            colour=discord.Colour(value=colour))

        charts = list()
        charts.append(kpopcharts.IChart(kpopcharts.ChartType.Week))
        normalized = kpopcharts.NormalizedChartList(*charts)

        for entry in normalized[0][:10]:
            if entry.change == "up":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↑{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            elif entry.change == "down":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↓{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            else:
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1}'.format(str(entry.artists), entry.title)), inline=False)

        if normalized[0][0].video != "":
            videoId = normalized[0][0].video.split("/")
            videoId = videoId[len(videoId)-1]
            data.set_thumbnail(url="https://img.youtube.com/vi/{}/hqdefault.jpg".format(videoId))

        data.set_footer(text="Time: {0} UTC".format(str(datetime.datetime.utcnow()).split('.', 1)[0].rsplit(':', 1)[0]))

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

    @charts.group(pass_context=True)
    async def melon(self, context):
        """Prints melon charts."""
        if str(context.invoked_subcommand) == "charts melon":
            await send_cmd_help(context)

    @melon.command(name="realtime")
    async def realtime_melon(self):
        """Get the Melon Realtime charts!"""
        
        await self.bot.type()

        colour = int("00CD3C", 16)

        data = discord.Embed(
            title="Melon Realtime Charts",
            url="http://www.melon.com/chart/index.htm",
            colour=discord.Colour(value=colour))

        charts = list()
        charts.append(kpopcharts.MelonChart(kpopcharts.ChartType.Realtime))
        normalized = kpopcharts.NormalizedChartList(*charts)

        for entry in normalized[0][:10]:
            if entry.change == "up":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↑{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            elif entry.change == "down":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↓{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            else:
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1}'.format(str(entry.artists), entry.title)), inline=False)

        data.set_footer(text="Time: {0} UTC".format(str(datetime.datetime.utcnow()).split('.', 1)[0].rsplit(':', 1)[0]))

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

    @melon.command(name="week")
    async def week_melon(self):
        """Get the Melon Week charts!"""
        
        await self.bot.type()

        colour = int("00CD3C", 16)

        data = discord.Embed(
            title="Melon Week Charts",
            url="http://www.melon.com/chart/week/index.htm",
            colour=discord.Colour(value=colour))

        charts = list()
        charts.append(kpopcharts.MelonChart(kpopcharts.ChartType.Week))
        normalized = kpopcharts.NormalizedChartList(*charts)

        for entry in normalized[0][:10]:
            if entry.change == "up":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↑{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            elif entry.change == "down":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↓{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            else:
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1}'.format(str(entry.artists), entry.title)), inline=False)

        data.set_footer(text="Time: {0} UTC".format(str(datetime.datetime.utcnow()).split('.', 1)[0].rsplit(':', 1)[0]))

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

    @charts.group(pass_context=True)
    async def gaon(self, context):
        """Prints gaon charts."""
        if str(context.invoked_subcommand) == "charts gaon":
            await send_cmd_help(context)

    @gaon.command(name="album")
    async def album_gaon(self):
        """Get the Gaon album charts!"""
        
        await self.bot.type()

        colour = int("000000", 16)

        data = discord.Embed(
            title="Gaon Album Week Charts",
            url="http://gaonchart.co.kr/main/section/chart/album.gaon?termGbn=week&nationGbn=T",
            colour=discord.Colour(value=colour))

        charts = list()
        charts.append(kpopcharts.GaonChart(kpopcharts.ChartType.AlbumWeek))
        normalized = kpopcharts.NormalizedChartList(*charts)

        for entry in normalized[0][:10]:
            if entry.change == "up":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↑{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            elif entry.change == "down":
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1} ↓{2}'.format(str(entry.artists), entry.title, entry.change_diff)), inline=False)
            else:
                data.add_field(name="#"+str(entry.rank), value=str('{0} - {1}'.format(str(entry.artists), entry.title)), inline=False)

        data.set_footer(text="Time: {0} UTC".format(str(datetime.datetime.utcnow()).split('.', 1)[0].rsplit(':', 1)[0]))

        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

def setup(bot):
    bot.add_cog(Charts(bot))
