import discord
from discord.ext import commands
from .utils.dataIO import fileIO
import os
import asyncio
import time
import logging

class RemindMe:
    """Never forget anything anymore."""

    def __init__(self, bot):
        self.bot = bot
        self.reminders = fileIO("data/remindme/reminders.json", "load")
        self.units = {"minute" : 60, "hour" : 3600, "day" : 86400, "week": 604800, "month": 2592000, "min":60, "hr":3600}

    @commands.command(pass_context=True)
    async def remindme(self, ctx,  quantity : int, time_unit : str, *, text : str):
        """Sends you <text> when the time is up

        Accepts: minutes, hours, days, weeks, month
        Example:
        [p]remindme 3 days Have sushi with Asu and JennJenn"""
        time_unit = time_unit.lower()
        author = ctx.message.author
        s = ""
        if time_unit.endswith("s"):
            time_unit = time_unit[:-1]
        if not time_unit in self.units:
            await self.bot.say("Invalid time unit. Choose minutes/hours/days/weeks/month")
            return
        if quantity < 1:
            await self.bot.say("Quantity must not be 0 or negative.")
            return
        if len(text) > 1960:
            await self.bot.say("Text is too long.")
            return
        if quantity !=1:
            s = "s"
        seconds = self.units[time_unit] * quantity
        future = int(time.time()+seconds)
        self.reminders.append({"ID" : author.id, "FUTURE" : future, "TEXT" : text})
        logger.info("{} ({}) set a reminder.".format(author.name, author.id))
        await self.bot.say("I will remind you about that in {} {}.".format(str(quantity), time_unit + s))
        fileIO("data/remindme/reminders.json", "save", self.reminders)

    @commands.command(pass_context=True)
    async def forgetme(self, ctx):
        """Removes all your upcoming notifications"""
        author = ctx.message.author
        to_remove = []
        for reminder in self.reminders:
            if reminder["ID"] == author.id:
                to_remove.append(reminder)

        if not to_remove == []:
            for reminder in to_remove:
                self.reminders.remove(reminder)
            fileIO("data/remindme/reminders.json", "save", self.reminders)
            await self.bot.say("All your notifications have been removed.")
        else:
            await self.bot.say("You don't have any upcoming notification.")
    
    @commands.command(pass_context=True)
    async def deleteme(self,ctx, idx : int):
        """Removes reminder number <idx> from your list of reminders"""
        author=ctx.message.author
        channel=ctx.message.channel
        reminders = []
        for reminder in self.reminders:
            if reminder["ID"] == author.id:
                reminders.append(reminder)
        reminders=sorted(reminders, key=lambda k: k['FUTURE'])
        if idx == 0:
            await self.bot.say("Invalid Input! idx has to be greather than 0")
        elif len(reminders) >= idx:
            #self.reminders.remove(reminders[idx-1])
            reminder=reminders[idx-1]
            s=reminder["FUTURE"]-int(time.time())
            m,s = divmod(s,60)
            h,m = divmod(m,60)
            d,h = divmod(h,24)
            timeString="";
            previous=0
            if d:
                timeString+=("{} days".format(d),"1 day") [d == 1]
                previous = 1
            if h:
                if previous:
                    timeString+=", "
                timeString+=("{} hours".format(h),"1 hour") [h == 1]
                previous = 1
            if m:
                if previous:
                    timeString+=", "
                timeString+=("{} minutes".format(m), " 1 minute") [m == 1]
                previous = 1
            if s:
                if previous:
                    timeString+=", "
                timeString+=("{} seconds".format(m), " 1 second") [s == 1]
            nextreminder="Removed reminder for `{1}` in `{0}`\n".format(timeString,reminder["TEXT"])
            await self.bot.send_message(author,nextreminder)
            self.reminders.remove(reminders[idx-1])
            fileIO("data/remindme/reminders.json", "save", self.reminders)
            if not channel.is_private:
                await self.bot.say("{0} Please check your DMs".format(author.mention))
        else:
            await self.bot.say("You don't have that many upcoming notifications.")

    @commands.command(pass_context=True)
    async def reminderlist(self, ctx):
        author=ctx.message.author
        channel=ctx.message.channel
        reminders = []
        for reminder in self.reminders:
            if reminder["ID"] == author.id:
                reminders.append(reminder)

        if not reminders == []:
            i=0
            msg=["```Reminders: \n"]
            for counter,reminder in enumerate(sorted(reminders, key=lambda k: k['FUTURE']) ):
                s=reminder["FUTURE"]-int(time.time())
                m,s = divmod(s,60)
                h,m = divmod(m,60)
                d,h = divmod(h,24)
                
                timeString=""
                previous = 0
                if d:
                    timeString+=("{} days".format(d),"1 day") [d == 1]
                    previous = 1
                if h:
                    if previous:
                        timeString+=","
                    timeString+=(" {} hours".format(h),"1 hour") [h == 1]
                    previous = 1
                if m:
                    if previous:
                        timeString+=","
                    timeString+=(" {} minutes".format(m), " 1 minute") [m == 1]
                    previous = 1
                if s:
                    if previous:
                        timeString+=","
                    timeString+=(" {} seconds".format(m), " 1 second") [s == 1]
                nextreminder="{2}. {0}:\n\t{1}\n".format(timeString,reminder["TEXT"],counter+1)
               
                if len(msg[i]) + len(ctx.prefix) + len(reminder) + 5 > 2000:
                    msg[i] += "```"
                    i += 1
                    msg.append("```"+nextreminder)
                else:
                    msg[i]+=nextreminder
            msg[i]+="```"
            for reminder in msg:
                await self.bot.send_message(author, reminder)
            if not channel.is_private:
                await self.bot.say("{0} Please check your DMs".format(author.mention))
        else:
            await self.bot.say("You don't have any upcoming notification.")

            
    async def check_reminders(self):
        while self is self.bot.get_cog("RemindMe"):
            to_remove = []
            for reminder in self.reminders:
                if reminder["FUTURE"] <= int(time.time()):
                    try:
                        await self.bot.send_message(discord.User(id=reminder["ID"]), ":alarm_clock: You asked me to remind you about this:\n```{}```".format(reminder["TEXT"]))
                    except (discord.errors.Forbidden, discord.errors.NotFound):
                        to_remove.append(reminder)
                    except discord.errors.HTTPException:
                        pass
                    else:
                        to_remove.append(reminder)
            for reminder in to_remove:
                self.reminders.remove(reminder)
            if to_remove:
                fileIO("data/remindme/reminders.json", "save", self.reminders)
            await asyncio.sleep(5)

def check_folders():
    if not os.path.exists("data/remindme"):
        print("Creating data/remindme folder...")
        os.makedirs("data/remindme")

def check_files():
    f = "data/remindme/reminders.json"
    if not fileIO(f, "check"):
        print("Creating empty reminders.json...")
        fileIO(f, "save", [])

def setup(bot):
    global logger
    check_folders()
    check_files()
    logger = logging.getLogger("remindme")
    if logger.level == 0: # Prevents the logger from being loaded again in case of module reload
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(filename='data/remindme/reminders.log', encoding='utf-8', mode='a')
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt="[%d/%m/%Y %H:%M]"))
        logger.addHandler(handler)
    n = RemindMe(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n.check_reminders())
    bot.add_cog(n)
