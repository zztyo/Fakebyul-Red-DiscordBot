import discord
from discord.ext import commands
from __main__ import send_cmd_help
import os
from .utils.dataIO import dataIO
from cogs.utils import checks

class Notifications:
    """Get notifications for keywords"""

    def __init__(self, bot):
        self.bot = bot
        self.keywords_file_path = "data/notifications/keywords.json"
        self.keywords = dataIO.load_json(self.keywords_file_path)

    @commands.group(pass_context=True, no_pm=True, name="notifications", aliases=["notification", "noti"])
    async def _notifications(self, ctx):
        """Get a dm when someone says a keyword"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_notifications.command(pass_context=True, no_pm=True, name="add")
    async def _add(self, ctx, *, keyword):
        """Adds a keyword to your list"""
        message = ctx.message
        author = ctx.message.author
        server = ctx.message.server

        keyword = keyword.strip().lower()

        if server.id not in self.keywords:
            self.keywords[server.id] = []

        for keywordData in self.keywords[server.id]:
            if keywordData["userId"] == author.id and keywordData["keyword"] == keyword:
                await self.bot.delete_message(message)
                await self.bot.say("{0} Please check your DMs".format(author.mention))
                await self.bot.send_message(author, "The keyword `{1}` is already in your list on the `{2.name}` server! :thinking:".format(author.mention, keyword, server))
                return

        keywordData = {"userId": author.id, "keyword": keyword}
        self.keywords[server.id].append(keywordData)

        dataIO.save_json(self.keywords_file_path, self.keywords)

        await self.bot.delete_message(message)
        await self.bot.say("{0} Please check your DMs".format(author.mention))
        await self.bot.send_message(author, "Added keyword `{1}` to your list on the `{2.name}` server! :ok_hand:".format(author.mention, keyword, server))

    @_notifications.command(pass_context=True, no_pm=True, name="del")
    async def _del(self, ctx, *, keyword):
        """Removes a keyword from your list"""
        message = ctx.message
        author = ctx.message.author
        server = ctx.message.server

        keyword = keyword.strip().lower()

        if server.id not in self.keywords:
            await self.bot.delete_message(message)
            await self.bot.say("{0} Please check your DMs".format(author.mention))
            await self.bot.send_message(author, "Unable to find keyword `{1}` in your list on the `{2.name}` server! :warning:".format(author.mention, keyword, server))
            return

        for keywordData in self.keywords[server.id]:
            if keywordData["userId"] == author.id and keywordData["keyword"] == keyword:
                del(self.keywords[server.id][self.keywords[server.id].index(keywordData)])
                dataIO.save_json(self.keywords_file_path, self.keywords)

                await self.bot.delete_message(message)
                await self.bot.say("{0} Please check your DMs".format(author.mention))
                await self.bot.send_message(author, "Removed keyword `{1}` from your list on the `{2.name}` server! :ok_hand:".format(author.mention, keyword, server))
                return

        await self.bot.delete_message(message)
        await self.bot.say("{0} Please check your DMs".format(author.mention))
        await self.bot.send_message(author, "Unable to find keyword `{1}` in your list on the `{2.name}` server! :warning:".format(author.mention, keyword, server))

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
        keywordsMessage += "on the `{0.name}` server.".format(server)

        await self.bot.say("{0} Please check your DMs".format(author.mention))
        await self.bot.send_message(author, keywordsMessage)

    @_notifications.group(pass_context=True, name="global")
    @checks.is_owner()
    async def _global(self, ctx):
        """Global notifications"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_global.command(pass_context=True, no_pm=True, name="add")
    @checks.is_owner()
    async def _global_add(self, ctx, *, keyword):
        """Adds a keyword to your global list"""
        message = ctx.message
        author = ctx.message.author
        server = ctx.message.server

        keyword = keyword.strip().lower()

        if "global" not in self.keywords:
            self.keywords["global"] = []

        for keywordData in self.keywords["global"]:
            if keywordData["userId"] == author.id and keywordData["keyword"] == keyword:
                await self.bot.say("{0} The keyword `{1}` is already in your **global** list! :thinking:".format(author.mention, keyword))
                return

        keywordData = {"userId": author.id, "keyword": keyword}
        self.keywords["global"].append(keywordData)

        dataIO.save_json(self.keywords_file_path, self.keywords)

        await self.bot.delete_message(message)
        await self.bot.say("{0} Please check your DMs".format(author.mention))
        await self.bot.send_message(author, "Added keyword `{1}` to your **global** list! :ok_hand:".format(author.mention, keyword))

    @_global.command(pass_context=True, no_pm=True, name="del")
    @checks.is_owner()
    async def _global_del(self, ctx, *, keyword):
        """Removes a keyword from your global list"""
        author = ctx.message.author
        server = ctx.message.server

        keyword = keyword.strip().lower()

        if "global" not in self.keywords:
            await self.bot.say("{0} Unable to find keyword `{1}` in your **global** list! :warning:".format(author.mention, keyword))
            return

        for keywordData in self.keywords["global"]:
            if keywordData["userId"] == author.id and keywordData["keyword"] == keyword:
                del(self.keywords["global"][self.keywords["global"].index(keywordData)])
                dataIO.save_json(self.keywords_file_path, self.keywords)

                await self.bot.say("{0} Removed keyword `{1}` from your **global** list! :ok_hand:".format(author.mention, keyword))
                return

        await self.bot.say("{0} Unable to find keyword `{1}` in your **global** list! :warning:".format(author.mention, keyword))

    @_global.command(pass_context=True, no_pm=True, name="list")
    @checks.is_owner()
    async def _global_list(self, ctx):
        """Shows all your global keywords"""
        author = ctx.message.author
        server = ctx.message.server

        if "global" not in self.keywords:
            await self.bot.say("{0} No keywords in your **global** list! :warning:".format(author.mention))
            return

        keywordsToPrint = []
        for keywordData in self.keywords["global"]:
            if keywordData["userId"] == author.id:
                keywordsToPrint.append(keywordData)

        if len(keywordsToPrint) <= 0:
            await self.bot.say("{0} No keywords in your **global** list! :warning:".format(author.mention))
            return

        keywordsMessage = "I will notify you **globally** for: "
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

        await self.bot.say("{0} Please check your DMs".format(author.mention))
        await self.bot.send_message(author, keywordsMessage)

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

        all_requested_keywords = []
        if server.id in self.keywords:
            all_requested_keywords += self.keywords[server.id]
        if "global" in self.keywords:
            all_requested_keywords += self.keywords["global"]

        if len(all_requested_keywords) <= 0:
            return

        toNotifyUserForList = {}
        for keywordData in all_requested_keywords:
            if self._words_in_text(message.content.lower(), keywordData["keyword"]):
                userToNotify = message.server.get_member(keywordData["userId"])
                if userToNotify == None:
                    print("user #{0[userId]} for keyword notification \"{0[keyword]}\" not found!")
                    continue

                if userToNotify == message.author:
                    continue

                userToNotifyPermissions = message.channel.permissions_for(userToNotify)
                if userToNotifyPermissions.read_message_history == True:
                    if keywordData["keyword"] not in toNotifyUserForList:
                        toNotifyUserForList[keywordData["keyword"]] = {userToNotify}
                    else:
                        toNotifyUserForList[keywordData["keyword"]].add(userToNotify)
        if len(toNotifyUserForList) > 0:
            keywordListText = ""
            i = 0
            for keyword, users in toNotifyUserForList.items():
                i += 1
                if i == 1:
                    keywordListText += "`{0}`".format(keyword)
                elif i < len(toNotifyUserForList):
                    keywordListText += ", `{0}`".format(keyword)
                else:
                    keywordListText += " and `{0}`".format(keyword)
            for user in users:
                notifyMessage = ":bell: User {0.author.name} ({0.author.mention}) mentioned {1} in {0.channel.mention} on the `{0.server.name}` server:\n```{0.content}```".format(message, keywordListText)
                await self.bot.send_message(user, notifyMessage)

    def _words_in_text(self, haystack, needle):
        if haystack == needle:
            return True
        if haystack.startswith(needle + " "):
            return True
        if haystack.endswith(" " + needle):
            return True
        if haystack.find(" " + needle + " ") != -1:
            return True
        if haystack.find(" " + needle + ",") != -1:
            return True
        if haystack.find("," + needle + " ") != -1:
            return True
        if haystack.find("\"" + needle + " ") != -1:
            return True
        if haystack.find(" " + needle + "\"") != -1:
            return True
        if haystack.find("\"" + needle + "\"") != -1:
            return True
        return False

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
