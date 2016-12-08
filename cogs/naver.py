import discord
from discord.ext import commands
import aiohttp
import asyncio
from __main__ import send_cmd_help
from .utils.chat_formatting import pagify, box

__author__ = "Sebastian Winkler <sekl@slmn.de>"
__version__ = "0.1"

class Naver:
    """I translate stuff using naver's neural machine translation service!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, aliases=["n"])
    async def naver(self, context):
        """Naver translation"""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @naver.command(pass_context=True, aliases=["ko"])
    async def korean(self, context, *text: str):
        """Translates korean into english"""

        text = ' '.join(text)
        await self.bot.type()
        if text != "":
            translation = "English translation:\n"
            n = 200
            for i in range(0, len(text), n):
                translation += await self._translate("ko", "en", str(text[i:i+n]))
                await asyncio.sleep(1)

            for page in pagify(translation, [" "]):
                if page != "":
                    await self.bot.say(box(page))
        else:
            await send_cmd_help(context)

    @naver.command(pass_context=True, aliases=["en"])
    async def english(self, context, *text: str):
        """Translates english into korean"""

        text = ' '.join(text)
        await self.bot.type()
        if text != "":
            translation = "Korean translation:\n"
            n = 200
            for i in range(0, len(text), n):
                translation += await self._translate("en", "ko", str(text[i:i+n]))
                await asyncio.sleep(1)

            for page in pagify(translation, [" "]):
                if page != "":
                    await self.bot.say(box(page))
        else:
            await send_cmd_help(context)

    async def _translate(self, source, target, text):
        url = "http://labspace.naver.com/api/n2mt/translate"

        payload = {"source": source, "target": target, "text": text}
        headers = {"user-agent": "Red-cog-Naver/"+__version__, "x-naver-client-id": "labspace"}
        try:
            conn = aiohttp.TCPConnector()
            session = aiohttp.ClientSession(connector=conn)
            async with session.post(url, data=payload, headers=headers) as r:
                result = await r.json()
            session.close()
            return result["message"]["result"]["translatedText"]
        except Exception as e:
            print("translation api error: {0}".format(e))
            return "Something went terribly wrong!"

def setup(bot):
    bot.add_cog(Naver(bot))
