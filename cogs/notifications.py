import discord
from discord.ext import commands
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO

class Notifications:
    """Get notifications for keywords"""

    def __init__(self, bot):
        self.bot = bot
        self.keywords_file_path = "data/notifications/keywords.json"
        self.keywords = dataIO.load_json(self.keywords_file_path)

    @commands.group(pass_context=True, no_pm=True, name="notifications", aliases=["notification"])
    async def _notifications(self, ctx):
        """Get a dm when someone says a keyword"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_notifications.command(pass_context=True, no_pm=True, name="add")
    async def _add(self, ctx, keyword : str):
        """Adds a keyword to your list"""
        author = ctx.message.author
        server = ctx.message.server

        keyword = keyword.strip().lower()

        if server.id not in self.keywords:
            self.keywords[server.id] = []

        for keywordData in self.keywords[server.id]:
            if keywordData["userId"] == author.id and keywordData["keyword"] == keyword:
                await self.bot.say("{0} The keyword `{1}` is already in your list! :thinking:".format(author.mention, keyword))
                return

        keywordData = {"userId": author.id, "keyword": keyword}
        self.keywords[server.id].append(keywordData)

        dataIO.save_json(self.keywords_file_path, self.keywords)

        await self.bot.say("{0} Added keyword `{1}` to your list! :ok_hand:".format(author.mention, keyword))

    @_notifications.command(pass_context=True, no_pm=True, name="del")
    async def _del(self, ctx, keyword : str):
        """Removed  keyword from  your list"""
        author = ctx.message.author
        server = ctx.message.server

        keyword = keyword.strip().lower()

        if server.id not in self.keywords:
            await self.bot.say("{0} Unable to find keyword `{1}` in your list! :warning:".format(author.mention, keyword))
            return

        for keywordData in self.keywords[server.id]:
            if keywordData["userId"] == author.id and keywordData["keyword"] == keyword:
                del(self.keywords[server.id][self.keywords[server.id].index(keywordData)])
                dataIO.save_json(self.keywords_file_path, self.keywords)

                await self.bot.say("{0} Removed keyword `{1}` from your list! :ok_hand:".format(author.mention, keyword))
                return

        await self.bot.say("{0} Unable to find keyword `{1}` in your list! :warning:".format(author.mention, keyword))

    @_notifications.command(pass_context=True, no_pm=True, name="list")
    async def _list(self, ctx):
        """Shows all your keywords"""
        author = ctx.message.author
        server = ctx.message.server

        if server.id not in self.keywords:
            await self.bot.say("{0} No keywords in your list! :warning:".format(author.mention))
            return

        keywordsToPrint = []
        for keywordData in self.keywords[server.id]:
            if keywordData["userId"] == author.id:
                keywordsToPrint.append(keywordData)

        if len(keywordsToPrint) <= 0:
            await self.bot.say("{0} No keywords in your list! :warning:".format(author.mention))
            return

        keywordsMessage = "I will notify you for: "
        i = 0
        for keyword in keywordsToPrint:
            i += 1
            if i == 1:
                keywordsMessage += "`{0[keyword]}`".format(keyword)
            elif i < len(keywordsToPrint):
                keywordsMessage += ", `{0[keyword]}`".format(keyword)
            else:
                keywordsMessage += " and `{0[keyword]}`".format(keyword)
        keywordsMessage += "."
        await self.bot.say("{0} {1}".format(author.mention, keywordsMessage))

    async def check_keyword(self, message):
        server = message.server
        author = message.author

        if message.server is None:
            return

        if message.channel.is_private:
            return

        if author == self.bot.user:
            return

        if self._is_command(message.content):
            return

        if server.id not in self.keywords:
            return

        messageList = message.content.lower().split()
        for keywordData in self.keywords[server.id]:
            if keywordData["keyword"] in messageList:
                userToNotify = message.server.get_member(keywordData["userId"])
                if userToNotify == None:
                    print("user #{0[userId]} for keyword notification \"{0[keyword]}\" not found!")
                    continue

                if userToNotify == message.author:
                    continue

                userToNotifyPermissions = message.channel.permissions_for(userToNotify)
                if userToNotifyPermissions.read_message_history == True:
                    # I can't link to channels in embeds :(
                    """
                    colour = int("FFAC33", 16)

                    data = discord.Embed(
                        title=":bell: notification for the keyword \"{0[keyword]}\"".format(keywordData),
                        url=message.author.default_avatar_url,
                        description=message.content,
                        colour=discord.Colour(value=colour))
                    data.set_author(name="message by {0.author.name}".format(message), icon_url=message.author.avatar_url

                    await self.bot.send_message(userToNotify, embed=data)
                    """
                    notifyMessage = ":bell: {0.author.name} mentioned `{1[keyword]}` in {0.channel.mention}:\n```{0.content}```".format(message, keywordData)
                    await self.bot.send_message(userToNotify, notifyMessage)

    def _is_command(self, msg):
        for p in self.bot.settings.prefixes:
            if msg.startswith(p):
                return True
        if msg.startswith("+") or msg.startswith("-"):
            return True
        return False

def check_folders():
    folders = ("data", "data/notifications/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def check_files():
    keywords = {}

    if not os.path.isfile("data/notifications/keywords.json"):
        print("Creating empty keywords.json...")
        dataIO.save_json("data/notifications/keywords.json", keywords)

def setup(bot):
    check_folders()
    check_files()
    n = Notifications(bot)
    bot.add_listener(n.check_keyword, "on_message")
    bot.add_cog(n)
