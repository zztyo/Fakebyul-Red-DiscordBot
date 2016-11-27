import discord
from discord.ext import commands
from random import choice as randchoice
from .utils import kpopcharts
import datetime
from __main__ import send_cmd_help

class Charts:
    """My custom cog that does stuff!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def charts(self, context):
        """Prints the current charts."""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @charts.command()
    async def ichart(self):
        """Get the latest iCharts charts!"""
        
        message = await self.bot.say("Thinking... :thinking:")

        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        data = discord.Embed(
            title="iChart Realtime",
            url="http://www.instiz.net/iframe_ichart_score.htm",
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

        #if thumbnail != "":
        #    data.set_thumbnail(url=thumbnail)

        data.set_footer(text="Time: {0} UTC".format(str(datetime.datetime.utcnow()).split('.', 1)[0].rsplit(':', 1)[0]))

        await self.bot.delete_message(message)
        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

    @charts.command(hidden=True)
    async def melon(self):
        """Get the latest Melon charts!"""
        
        message = await self.bot.say("Thinking... :thinking:")

        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        data = discord.Embed(
            title="Melon Realtime",
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

        #if thumbnail != "":
        #    data.set_thumbnail(url=thumbnail)

        data.set_footer(text="Time: {0} UTC".format(str(datetime.datetime.utcnow()).split('.', 1)[0].rsplit(':', 1)[0]))

        await self.bot.delete_message(message)
        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

    @charts.command()
    async def gaon(self):
        """Get the latest Gaon charts!"""
        
        message = await self.bot.say("Thinking... :thinking:")

        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        data = discord.Embed(
            title="Gaon Albums Weekly",
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

        #if thumbnail != "":
        #    data.set_thumbnail(url=thumbnail)

        data.set_footer(text="Time: {0} UTC".format(str(datetime.datetime.utcnow()).split('.', 1)[0].rsplit(':', 1)[0]))

        await self.bot.delete_message(message)
        try:
            await self.bot.say(embed=data)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")

def setup(bot):
    bot.add_cog(Charts(bot))
