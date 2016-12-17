import discord
from discord.ext import commands
from __main__ import send_cmd_help
from .utils import GfycatApi

# /gfy crt https://www.instagram.com/p/BOG7-gfg_O2/?taken-by=s_sohye
class Gfycat:
    """gfycat cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, name='gfycat', aliases=['gfy'])
    async def _gfycat(self, ctx):
        """Does gfycat stuff"""

        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_gfycat.command(pass_context=True, name='create', aliases=['crt'])
    async def _create(self, ctx, url : str):
        """Creates a gfycat from a url"""
        author = ctx.message.author

        if url == "":
            await send_cmd_help(ctx)
            return

        statusMessage = await self.bot.say("Talking to gfycat.com... :telephone:")
        upload = await GfycatApi.GfycatApi().upload(url)
        print(upload)

        if "gfyName" not in upload:
            await self.bot.say("{0.mention} Something went wrong! :warning:".format(author))
            return

        gfycatUrl = "https://gfycat.com/{0}".format(upload["gfyName"])
        await self.bot.say("{0.mention} Your gfycat: {1}".format(author, gfycatUrl))


def setup(bot):
    bot.add_cog(Gfycat(bot))
