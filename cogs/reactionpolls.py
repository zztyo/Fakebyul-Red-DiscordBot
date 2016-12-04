import discord
import os
from .utils.dataIO import dataIO
from discord.ext import commands
from __main__ import send_cmd_help
from random import choice as randchoice
from cogs.utils import checks

class ReactionPolls:
    """Create reaction polls!"""

    def __init__(self, bot):
        self.bot = bot
        self.polls_file_path = "data/reactionpolls/polls.json"
        self.polls = dataIO.load_json(self.polls_file_path)

    @commands.group(pass_context=True, no_pm=True, aliases=['rp'])
    async def reactionpoll(self, ctx):
        """Manage reaction polls"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @reactionpoll.command(pass_context=True, no_pm=True, aliases=['crt'])
    async def create(self, ctx, question: str, maxReactions: int, *allowedEmojis: str):
        """Create a new reaction poll
        maxReactions: 0 = unlimited"""
        message = ctx.message
        author = message.author

        pollNumber = str(len(self.polls)+1)
        while True:
            if pollNumber in self.polls:
                pollNumber = str(int(pollNumber)+1)
            else:
                break

        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        if question == "" or len(allowedEmojis) <= 0:
            await send_cmd_help(ctx)
            return

        data = discord.Embed(
            description=str("Poll #{0}").format(pollNumber),
            colour=discord.Colour(value=colour))
        data.set_author(name=str(question))
        data.set_footer(text="Poll by {0}".format(author.name), icon_url=author.avatar_url)

        try:
            pollMessage = await self.bot.say(embed=data)
            for emoji in allowedEmojis:
                customEmoji = self.getCustomEmoji(emoji)
                if customEmoji == None:
                    await self.bot.add_reaction(pollMessage, emoji)
                else:
                    allowedEmojis = tuple(x for x in allowedEmojis if x != emoji)
                    allowedEmojis = allowedEmojis + (emoji,)
                    await self.bot.add_reaction(pollMessage, customEmoji)
        except discord.HTTPException as e:
            print(e)
            await self.bot.say("I need the `Embed links` permission "
                               "to send this or you send misformatted arguments")
            return
        self.polls[pollNumber] = {"messageId": pollMessage.id, "allowedEmojis": allowedEmojis, "status": "active", "createdBy": author.id, "maxReactions": maxReactions}
        dataIO.save_json(self.polls_file_path, self.polls)

    def getCustomEmoji(self, emojiStr):
        allCustomEmojis = list(self.bot.get_all_emojis())
        for customEmoji in allCustomEmojis:
            if customEmoji.require_colons:
                if "<:{0}:{1}>".format(customEmoji.name, customEmoji.id) == emojiStr:
                    return customEmoji
            else:
                if "<:{0}:{1}>".format(customEmoji.name, customEmoji.id) == emojiStr:
                    return customEmoji
        return None

    @reactionpoll.command(pass_context=True, no_pm=True, aliases=['del'])
    async def delete(self, ctx, pollId: str):
        """Deletes a poll from the db (doesn't delete the chat message!)"""
        message = ctx.message
        author = message.author
        try:
            pollId = str(pollId.replace("#", ""))
            self.bot.say(pollId)
        except ValueError:
            await self.bot.say("You have to tell me the poll id... :thinking:")
            return

        if str(pollId) not in self.polls:
            await self.bot.say("Unable to find poll! :scream:")
            return

        poll = self.polls[str(pollId)]

        if poll["createdBy"] != author.id:# and not checks.mod_or_permissions(manage_messages=True):
            await self.bot.say("You are not allowed to delete this reaction poll... :warning:")
            return

        del self.polls[str(pollId)]
        dataIO.save_json(self.polls_file_path, self.polls)
        await self.bot.say("Poll deleted from database! :wave:")

    @reactionpoll.command(pass_context=True, no_pm=True, aliases=['frz'])
    async def freeze(self, ctx, pollId: str):
        """Toggles the state of a poll
        Nobody can add reactions to freezed polls (removal of reactions is still possible!)
        """
        message = ctx.message
        author = message.author
        try:
            pollId = str(pollId.replace("#", ""))
            self.bot.say(pollId)
        except ValueError:
            await self.bot.say("You have to tell me the poll id... :thinking:")
            return

        if str(pollId) not in self.polls:
            await self.bot.say("Unable to find poll! :scream:")
            return

        poll = self.polls[str(pollId)]

        if poll["createdBy"] != author.id:# and not checks.mod_or_permissions(manage_messages=True):
            await self.bot.say("You are not allowed to manage this reaction poll... :warning:")
            return

        if poll["status"] == "active":
            self.polls[str(pollId)]["status"] = "freezed"
            await self.bot.say("Poll freezed! :snowflake:")
        else:
            self.polls[str(pollId)]["status"] = "active"
            await self.bot.say("Poll unfreezed! :zap:")

        dataIO.save_json(self.polls_file_path, self.polls)

    async def numberOfReactionsByUserOnMessage(self, message, user):
        i = 0
        for reaction in message.reactions:
            reactionUsers = await self.bot.get_reaction_users(reaction, limit=100)
            # todo: pagifying for more than 100 reactions
            if user in reactionUsers:
                i += 1
        return i

    async def check_reaction(self, reaction, user):
        for key in self.polls:
            poll = self.polls[key]
            if poll["messageId"] == reaction.message.id:
                emoji = self.getCustomEmoji(reaction.emoji)
                if emoji == None:
                    emoji = reaction.emoji
                reactionsByUser = await self.numberOfReactionsByUserOnMessage(reaction.message, user)
                if user != self.bot.user and (str(emoji) not in poll["allowedEmojis"] or (poll["maxReactions"] != 0 and reactionsByUser > poll["maxReactions"]) or poll["status"] != "active"):
                    try:
                        await self.bot.remove_reaction(reaction.message, reaction.emoji, user)
                    except Exception as e:
                        print(e)

def check_folder():
    if not os.path.exists("data/reactionpolls"):
        print("Creating data/reactionpolls folder...")
        os.makedirs("data/reactionpolls")


def check_file():
    polls = {}

    f = "data/reactionpolls/polls.json"
    if not dataIO.is_valid_json(f):
        print("Creating default reactionpolls polls.json...")
        dataIO.save_json(f, polls)

def setup(bot):
    check_folder()
    check_file()
    n = ReactionPolls(bot)
    bot.add_listener(n.check_reaction, "on_reaction_add")
    bot.add_cog(n)
