import asyncio
import os
from .utils.dataIO import dataIO
import discord
from discord.ext import commands
import json
import re
from __main__ import send_cmd_help,settings
import time
from .utils import checks
import aiohttp
from aiohttp.helpers import FormData

__author__ = "Alvin Wong <awong.1@alumni.ubc.ca>"
__version__ = "0.1"

class Hopper:
    """Tracks Kev's bias hopping"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/hopper/hops.json"
        self.hops=dataIO.load_json(self.file_path)
        self.settings_path="data/hopper/settings.json"
        self.settings=dataIO.load_json(self.settings_path)

    @commands.group(pass_context=True, no_pm=True, name="hops", hidden=True)
    async def _hops (self,ctx):
        """Tracks Kev's Waifuhopping"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @commands.command(pass_context=True,no_pm=True, hidden=True)
    async def waifuhopper(self,ctx):
        return await self._list.callback(self,ctx)

    @_hops.command(pass_context=True, no_pm=True, name = "list")
    async def _list(self,ctx):
        """Lists all of Kev's previous hops"""
        server=ctx.message.server
        if server.id !=self.settings["SERVER"]:
            return
        hoplist="```**Kev's Bias Hops**\n"
        for hop in self.hops["PREVIOUS"]:
            hoplist+="{}>".format(hop)
        hoplist+=self.hops["RECENT"]["ROLE"]
        hoplist+="```"
        await self.respond(ctx.message.channel,hoplist)

    @_hops.command(pass_context=True, no_pm=True, name = "add")
    async def _add(self, ctx,*, hop):
        """Add new hop"""
        server=ctx.message.server
        author=ctx.message.author
        if server.id !=self.settings["SERVER"] :
            return
        if author.id == self.settings["HOPPER"]:
            await self.respond(ctx.message.channel,"<:doyeonthink:267284550219071488> Kev why are you adding to your own criminal record")
            return
        if self.hops["RECENT"]["ROLE"].strip().lower()==hop.strip().lower():
             await self.respond(ctx.message.channel,"I already recorded that!")
             return
        await self._recentToPrevious()
        self.hops["RECENT"]={"ROLE":hop,"TIME": int(time.time())}
        dataIO.save_json(self.file_path,self.hops)
        await self.respond(ctx.message.channel,"Successfully added {} to the list".format(hop))
    
    
    @_hops.command(pass_context=True,no_pm=True, name = "remove", hidden =True)
    async def _remove(self,ctx, idx: int):
        await self._del.callback(self,ctx,idx)

    @_hops.command(pass_context=True,no_pm=True, name = "del", hidden = True)
    async def _del(self,ctx, idx: int):
        """ Removes previous hops from records

        Used in case of troll adds"""
        server=ctx.message.server
        author=ctx.message.author
        if server != self.settings["SERVER"]:
            return
        
        if author.id == self.settings["HOPPER"]:
            await self.respond(ctx.message.channel,"Kev pls you can't erase what you did <:chaekek:257245836789022720>")
            return
        
        if not self.permissions(ctx):
            await self.bot.say("You can't use this command")
            return
        removed=""
        if idx<len(self.hops["PREVIOUS"]):
            idx-=1
            removed=self.hops["PREVIOUS"].pop(idx)
        else:
            role=self.hops["PREVIOUS"].pop()
            removed = self.hops["RECENT"]["ROLE"]
            self.hops["RECENT"]["ROLE"]=role
        dataIO.save_json(self.file_path,self.hops)
        await self.respond(ctx.message.channel,"Removed {} from the list".format(removed))    
        

    @_hops.command(pass_context=True, no_pm=True, hidden=True,name="toggle")
    async def _toggle(self,ctx, toggle: str=None):
        """Turn on/off trash responses"""
        if server != self.settings["SERVER"] or not self.permissions(ctx):
            return
        if toggle=="off":
            self.settings["FANCY_RESPONSE"]=False
        elif toggle=="on":
            self.settings["FANCY_RESPONSE"]=True
        elif str is None:
            if self.settings["FANCY_RESPONSE"]:
                self.settings["FANCY_RESPONSE"]=False
                toggle="off"
            else:
                self.settings["FANCY_RESPONSE"]=True
                toggle="on"
        else:
            await send_cmd_help(ctx)
            return
        dataIO.save_json(self.file_path,self.settings)
        await self.bot.say("Turned {} Trash responses".format(toggle))

    @_hops.command(pass_context=True, no_pm=True, hidden=True,name="approve")
    async def _approve(self,ctx, user: discord.Member):
        
        if not self.permissions(ctx) or server != self.settings["SERVER"]:
            return
        if user.id not in self.settings["APPROVED"]:
            self.settings["APPROVED"].append(user.id)
            dataIO.save_json(self.file_path,self.settings)
            await self.respond(ctx.message.channel,"{} now has permission to edit the hopping list".format(user.display_name))
        else:
            await self.respond(ctx.message.channel,"{} was already approved".format(user.display_name))

    @_hops.command(pass_context=True, no_pm=True, hidden=True,name="unapprove")
    async def _unapprove(self,ctx, user: discord.Member):
        if author.id != settings.owner or server != self.settings["SERVER"] or author.id!=self.settings["TRASH"]:
                return

        if not self.permissions(ctx):
            await self.bot.say("You don't have permissions to use this command")
            return
        if user.id not in self.settings["APPROVED"]:
            await self.respond(ctx.message.channel,"{} never had permissions to edit the list <:chaekek:257245836789022720>".format(user.display_name))
        

    def permissions(self,ctx):
        author=ctx.message.author
        if author.id in self.settings["APPROVED"] or author.id==self.settings["TRASH"]:
            return True
        return False

    async def respond(self,channel, msg):
        if not self.settings["FANCY_RESPONSE"]:
            await self.bot.send_message(channel,msg)
            return
        headers = {"user-agent": "Red-cog-Mod/1", "content-type": "application/json", "Authorization": "Bot " + self.bot.settings.token}
        url  = "https://discordapp.com/api/channels/{0.id}/webhooks".format(channel)
        payload = {"name": "Robyul/Hopper: Response webhook"}
        conn = aiohttp.TCPConnector(verify_ssl=False)
        session = aiohttp.ClientSession(connector=conn)
        async with session.post(url, data=json.dumps(payload), headers=headers) as r:
            resultWebhookObject = await r.json()
        if "token" in resultWebhookObject and "id" in resultWebhookObject:
            url = "https://discordapp.com/api/webhooks/{0[id]}/{0[token]}".format(resultWebhookObject)
            trash=await self.bot.get_user_info(self.settings["TRASH"])
            payload = {"username": trash.display_name, "avatar_url": trash.avatar_url, "content": msg}
            async with session.post(url, data=json.dumps(payload), headers=headers) as r:
                result = await r.text()
            await asyncio.sleep(2)
            url = "https://discordapp.com/api/webhooks/{0[id]}/{0[token]}".format(resultWebhookObject)
            payload = {}
            async with session.delete(url, data=json.dumps(payload), headers=headers) as r:
                await r.text()
        else:
            await self.bot.send_message(channel,msg)

    async def checkHopped(self,before,after):
        a="a"
        

    async def _recentToPrevious(self):
        recent=self.hops["RECENT"]["ROLE"]
        self.hops["PREVIOUS"].append(recent)
        dataIO.save_json("self.file_path",self.hops)

def check_folders():
    if not os.path.exists("data/hopper"):
        print("Creating data/hopper folder...")
        os.makedirs("data/hopper")

def check_files():
    hops={
        "RECENT":{"ROLE":"",
                  "TIME":""},
        "PREVIOUS":[]
    }
    f = "data/hopper/hops.json"
    if not dataIO.is_valid_json(f):
        print("Creating default hops.json...")
        dataIO.save_json(f, hops)
    settings={
        "APPROVED":[],
        "FANCY_RESPONSE":True,
        "SERVER":"",
        "TRASH":"",
        "HOPPER":""
    }
    f = "data/hopper/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating default settings.json...")
        dataIO.save_json(f, settings)

def setup(bot):
    check_folders()
    check_files()
    n = Hopper(bot)
    bot.add_listener(n.checkHopped, "on_member_update")
    bot.add_cog(n)
        