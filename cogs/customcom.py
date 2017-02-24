from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks
from __main__ import user_allowed, send_cmd_help
import os
import re
from .utils.chat_formatting import pagify

class CustomCommands:
    """Custom commands."""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/customcom/commands.json"
        self.c_commands = dataIO.load_json(self.file_path)

    @commands.group(pass_context=True, no_pm=True, name="commands")
    async def _commands(self, ctx):
        """Custom commands."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_commands.command(pass_context=True, no_pm=True, name="add")
    @checks.mod_or_permissions(administrator=True)
    async def _add(self, ctx, command : str, *, text):
        """Adds a custom command

        Example:
        /commands add yourcommand Text you want
        """
        return await self.addcom.callback(self=self, ctx=ctx, command=command, text=text)

    @_commands.command(pass_context=True, no_pm=True, name="edit")
    @checks.mod_or_permissions(administrator=True)
    async def _edit(self, ctx, command : str, *, text):
        """Edits a custom command

        Example:
        /commands edit yourcommand Text you want
        """
        return await self.editcom.callback(self=self, ctx=ctx, command=command, text=text)

    @_commands.command(pass_context=True, no_pm=True, name="del")
    @checks.mod_or_permissions(administrator=True)
    async def _del(self, ctx, command : str):
        """Deletes a custom command

        Example:
        /commands del yourcommand"""
        return await self.delcom.callback(self=self, ctx=ctx, command=command)

    @_commands.command(pass_context=True, no_pm=True, name="list")
    async def _list(self, ctx):
        """Shows custom commands list"""
        return await self.customcommands.callback(self=self, ctx=ctx)
        
    @_commands.command(pass_context=True, no_pm=True, name="count")
    async def _count(self, ctx):
        """Searches in the custom commands"""
        server = ctx.message.server
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if cmdlist:
                if len(cmdlist)==1:
                    msg = "```There is 1 custom command on this server```"
                else:
                    msg="```There are {} custom commands on this server```".format(len(cmdlist))
                await self.bot.say(msg);
            else:
                await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")
        else:
            await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")

    @_commands.command(pass_context=True, no_pm=True, name="search")
    async def _search(self, ctx, keyword : str):
        """Searches in the custom commands"""
        server = ctx.message.server
        if keyword == "":
            await send_cmd_help(ctx)
            return
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if cmdlist:
                i = 0
                commandsFound = 0
                msg = ["```Custom commands with \"{0}\":\n".format(keyword)]
                for cmd in sorted([cmd for cmd in cmdlist.keys()]): 
                    if keyword not in cmd:
                        continue
                    commandsFound += 1
                    if len(msg[i]) + len(ctx.prefix) + len(cmd) + 5 > 2000:
                        msg[i] += "```"
                        i += 1
                        msg.append("``` {}{}\n".format(ctx.prefix, cmd))
                    else:
                        msg[i] += " {}{}\n".format(ctx.prefix, cmd)
                msg[i] += "```"
                if commandsFound <= 0:
                    await self.bot.say("There are no custom commands with that keyword in this server. Use addcom [command] [text]")
                    return
                for cmds in msg:
                    await self.bot.say(cmds)
            else:
                await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")
        else:
            await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")

    """
    @_commands.command(pass_context=True, no_pm=True, name="full-list")
    async def _full_list(self, ctx):
        ""Shows custom commands with their contents, can consume much traffic!""
        server = ctx.message.server
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if cmdlist:
                msg = "`Custom commands:`\n"
                await self.bot.send_message(ctx.message.author, msg)
                for cmd in sorted([cmd for cmd in cmdlist.keys()]):
                    msg = " `{}{}:`\n".format(ctx.prefix, cmd)
                    msg += "{}\n".format(self.format_cc(cmdlist[cmd], ctx.message))
                    await self.bot.send_message(ctx.message.author, msg)
            else:
                await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")
        else:
            await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")
    """

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @checks.mod_or_permissions(administrator=True)
    async def addcom(self, ctx, command : str, *, text):
        """Adds a custom command

        Example:
        /addcom yourcommand Text you want
        """
        server = ctx.message.server
        command = command.lower()
        if command in self.bot.commands.keys():
            await self.bot.say("That command is already a standard command.")
            return
        if not server.id in self.c_commands:
            self.c_commands[server.id] = {}
        cmdlist = self.c_commands[server.id]
        if command not in cmdlist:
            cmdlist[command] = text
            self.c_commands[server.id] = cmdlist
            dataIO.save_json(self.file_path, self.c_commands)
            await self.bot.say("Custom command successfully added.")
        else:
            await self.bot.say("This command already exists. Use editcom to edit it.")

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @checks.mod_or_permissions(administrator=True)
    async def editcom(self, ctx, command : str, *, text):
        """Edits a custom command

        Example:
        /editcom yourcommand Text you want
        """
        server = ctx.message.server
        command = command.lower()
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if command in cmdlist:
                cmdlist[command] = text
                self.c_commands[server.id] = cmdlist
                dataIO.save_json(self.file_path, self.c_commands)
                await self.bot.say("Custom command successfully edited.")
            else:
                await self.bot.say("That command doesn't exist. Use addcom [command] [text]")
        else:
             await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @checks.mod_or_permissions(administrator=True)
    async def delcom(self, ctx, command : str):
        """Deletes a custom command

        Example:
        /delcom yourcommand"""
        server = ctx.message.server
        command = command.lower()
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if command in cmdlist:
                cmdlist.pop(command, None)
                self.c_commands[server.id] = cmdlist
                dataIO.save_json(self.file_path, self.c_commands)
                await self.bot.say("Custom command successfully deleted.")
            else:
                await self.bot.say("That command doesn't exist.")
        else:
            await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    async def customcommands(self, ctx):
        """Shows custom commands list"""
        server = ctx.message.server
        author = ctx.message.author
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if cmdlist:
                i = 0
                msg = ["```Custom commands:\n"]
                for cmd in sorted([cmd for cmd in cmdlist.keys()]):
                    if len(msg[i]) + len(ctx.prefix) + len(cmd) + 5 > 2000:
                        msg[i] += "```"
                        i += 1
                        msg.append("``` {}{}\n".format(ctx.prefix, cmd))
                    else:
                        msg[i] += " {}{}\n".format(ctx.prefix, cmd)
                msg[i] += "```"
                for cmds in msg:
                    await self.bot.whisper(cmds)
                await self.bot.say("{0} Please check your DMs".format(author.mention))
            else:
                await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")
        else:
            await self.bot.say("There are no custom commands in this server. Use addcom [command] [text]")

    async def checkCC(self, message):
        if len(message.content) < 2 or message.channel.is_private:
            return

        server = message.server
        prefix = self.get_prefix(message)

        if not prefix:
            return

        if server.id in self.c_commands and user_allowed(message):
            cmdlist = self.c_commands[server.id]
            cmd = message.content[len(prefix):]
            if cmd in cmdlist.keys():
                cmd = cmdlist[cmd]
                cmd = self.format_cc(cmd, message)
                await self.bot.send_message(message.channel, cmd)
            elif cmd.lower() in cmdlist.keys():
                cmd = cmdlist[cmd.lower()]
                cmd = self.format_cc(cmd, message)
                await self.bot.send_message(message.channel, cmd)

    def get_prefix(self, message):
        for p in self.bot.settings.get_prefixes(message.server):
            if message.content.startswith(p):
                return p
        return False

    def format_cc(self, command, message):
        results = re.findall("\{([^}]+)\}", command)
        for result in results:
            param = self.transform_parameter(result, message)
            command = command.replace("{" + result + "}", param)
        return command

    def transform_parameter(self, result, message):
        """
        For security reasons only specific objects are allowed
        Internals are ignored
        """
        raw_result = "{" + result + "}"
        objects = {
            "message" : message,
            "author"  : message.author,
            "channel" : message.channel,
            "server"  : message.server
        }
        if result in objects:
            return str(objects[result])
        try:
            first, second = result.split(".")
        except ValueError:
            return raw_result
        if first in objects and not second.startswith("_"):
            first = objects[first]
        else:
            return raw_result
        return str(getattr(first, second, raw_result))


def check_folders():
    if not os.path.exists("data/customcom"):
        print("Creating data/customcom folder...")
        os.makedirs("data/customcom")

def check_files():
    f = "data/customcom/commands.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty commands.json...")
        dataIO.save_json(f, {})

def setup(bot):
    check_folders()
    check_files()
    n = CustomCommands(bot)
    bot.add_listener(n.checkCC, "on_message")
    bot.add_cog(n)
