from discord.ext import commands
from util import formats
from cleverbot import Cleverbot
from util.checks import PermissionError

import traceback
import discord
import aiohttp
import json
import asyncio
import time
import datetime
import random

class Core(object):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.uptime = time.time()
        self.instances = {}
        self.bot.loop.create_task(self.update())
        self.bot.loop.create_task(self.game_changer())

    def __unload(self):
        self.bot.loop.create_task(self.session.close())

    async def game_changer(self):
        while True:

            servers = 0
            users = 0
            channels = 0
            voice_states = 0

            for key in await self.bot.db.redis.keys("shard-*:*"):
                value = await self.bot.db.redis.get(key)
                if key.endswith("channels"):
                    channels += int(value)

                if key.endswith("servers"):
                    servers += int(value)

                if key.endswith("users"):
                    users += int(value)

                if key.endswith("voice_states"):
                    voice_states += int(value)

            playing_list = [
                "{0} servers".format(servers),
                "{0} users".format(users),
                "{0} channels".format(channels),
                "music on {0} servers".format(voice_states),
                "music better than aethex",
                "dank memes 24/7",
                "beemo.club",
                "autoplay on donator guilds",
                "music on Beemo's HQ",
                "shard {0}/{1}".format(self.bot.shard_id+1, self.bot.shard_count),
                "music on the dance floor",
                "video games",
            ]

            for playing_game in random.sample(playing_list, len(playing_list)):
                forced_play = await self.bot.db.redis.get("config:playing_status")
                if forced_play is not None:
                    playing_game = forced_play

                playing_game = "{0} | {1}help | {1}invite".format(playing_game, self.bot.default_prefix[0])

                await self.bot.change_presence(game=discord.Game(name=playing_game))
                await asyncio.sleep(30)

    @commands.command(aliases=["info", "botinfo"], pass_context=True)
    async def stats(self, ctx):
        """Returns bot statistics"""
        servers = 0
        users = 0
        channels = 0
        voice_states = 0

        for key in await self.bot.db.redis.keys("shard-*:*"):
            value = await self.bot.db.redis.get(key)
            if key.endswith("channels"):
                channels += int(value)

            if key.endswith("servers"):
                servers += int(value)

            if key.endswith("users"):
                users += int(value)

            if key.endswith("voice_states"):
                voice_states += int(value)

        uptime = str(datetime.timedelta(seconds=int(time.time()-self.uptime)))

        cached_searches = await self.bot.db.cache_redis.keys("*")
        cached_searches = len(cached_searches)

        database_info = await self.bot.db.redis.info("default")

        entries = [
            ("Library", "discord.py"),
            ("Owner", "minemidnight#0001"),
            ("Uptime", uptime),
            ("Shard ID", self.bot.shard_id),
            ("Shards", self.bot.shard_count),
            ("Servers", servers),
            ("Channels", channels),
            ("Users", users),
            ("Voice States", voice_states)
        ]

        colour = discord.Colour(0)
        if ctx.message.server is not None:
            colour = ctx.message.server.me.top_role.colour

        if colour == discord.Colour(0):
            #make it the green colour 
            colour = discord.Colour(0x2ecc71)

        await formats.embed(
            self.bot,
            entries,
            thumbnail=self.bot.user.avatar_url,
            colour=colour,
            description="A multi-purpose bot for discord.",
            title="Beemo Statistics",
            url="https://status.beemo.club"
        )
    async def update(self):
        if (await self.bot.db.redis.get("config:discord_bots_auth")) is not None:
            payload = json.dumps({
                "shard_id": int(self.bot.shard_id),
                "shard_count": int(self.bot.shard_count),
                "server_count": len(self.bot.servers)
            })

            headers = {
                "Authorization": await self.bot.db.redis.get("config:discord_bots_auth"),
                "content-type": "application/json"
            }

            url = "https://bots.discord.pw/api/bots/{0}/stats".format(self.bot.user.id)

            resp = await self.session.post(url, data=payload, headers=headers)
            resp.close()

        if (await self.bot.db.redis.get("config:carbonitex_key")) is not None:

            payload = {
                "key": await self.bot.db.redis.get("config:carbonitex_key"),
                "servercount": len(self.bot.servers),
                "shard_id": self.bot.shard_id,
                "shard_count": self.bot.shard_count
            }

            url = "https://www.carbonitex.net/discord/data/botdata.php"

            resp = await self.session.post(url, data=payload)
            resp_text = await resp.text()
            print(resp_text)
            resp.close()

    async def on_server_join(self, server):
        await self.update()

    async def on_server_leave(self, server):
        await self.update()

    @commands.command(aliases=["cinfo", "commandinfo", "desc"])
    async def describe(self, command : str):
        """Displays info about a command"""
        command = self.bot.get_command(command)
        if command is None:
            await self.bot.say("Command not found.")
            return

        entries = [
            ("Name", command.name),
            ("Aliases", ", ".join(command.aliases) if command.aliases else "None"),
            ("Info", command.help),
            ("No PM", command.no_pm),
            ("Module", command.module.__name__)
        ]

        await formats.describe_format(self.bot, entries)

    async def on_command_error(self, exception, ctx):

        #print(isinstance(exception, discord.ext.commands.errors.CommandInvokeError)) 
        #^ Returns true when something is raised in "group function"

        if isinstance(exception, commands.errors.MissingRequiredArgument):
            await self.bot.send_message(ctx.message.channel, exception.__str__())

        elif isinstance(exception, commands.errors.CommandNotFound):
            if ctx.prefix is not self.bot.default_prefix[0]:
                await self.bot.send_typing(ctx.message.channel)

                if ctx.message.author.id not in self.instances.keys():
                    future = self.bot.loop.run_in_executor(None, Cleverbot)
                    self.instances[ctx.message.author.id] = await future

                question = ctx.message.content.lstrip(str(ctx.prefix)+str(ctx.command)+" ")
                #print(question)
                future = self.bot.loop.run_in_executor(None, self.instances[ctx.message.author.id].ask, question)
                answer = await future
                await self.bot.send_message(ctx.message.channel, answer)
        elif isinstance(exception, commands.NoPrivateMessage):
            await self.bot.send_message(ctx.message.channel, "This command can't be used in Private Message.")
        elif isinstance(exception, PermissionError):
            await self.bot.send_message(ctx.message.channel, str(exception))
        elif isinstance(exception, commands.errors.CheckFailure):
            pass
        elif isinstance(exception, commands.errors.BadArgument):
            await self.bot.send_message(ctx.message.channel, "Bad command argument.")
        elif isinstance(exception, discord.errors.Forbidden):
            pass
        elif isinstance(exception, discord.errors.NotFound):
            pass
        else:
            text = "```"+"".join(traceback.format_exception(type(exception), exception, exception.__traceback__))+"```"
            print(text)
            await self.bot.wh.log(text)

    @commands.command(aliases=["get", "support"])
    async def invite(self):
        """Returns OAuth link and Beemo's HQ invite link."""
        client_id = await self.bot.db.redis.get("config:client_id")
        link = discord.utils.oauth_url(client_id, permissions=discord.Permissions(-1), redirect_uri="https://beemo.club")
        _message = "You can invite me using this link: {0}\nYou can also join my server using the link https://discord.gg/t5ddWzZ"
        await self.bot.say(_message.format(link))

    @commands.command(hidden=True)
    async def ping(self):
        lag = time.time()
        _message = await self.bot.say("ping")
        lag = int((time.time() - lag) * 1000)
        await self.bot.edit_message(_message, "pong `{0}ms`".format(lag))




def setup(bot):
    bot.add_cog(Core(bot))
