from discord.ext import commands
from discord.ext.commands.bot import _mentions_transforms
from .database import DB
from util.paste import paste
from .webhook import WebHook
from .prefix import server_prefix

import traceback
import discord
import asyncio
import aioredis
import json
import redis
import copy
import os
import glob

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

class Beemo(commands.Bot):
    ready = False
    def __init__(self, shard_id, **kwargs):
        self.db = DB(shard_id=shard_id, **kwargs)
        self.wh = WebHook(self.db.redis.get("config:webhook"), shard_id)
        self.default_prefix = json.loads(self.db.redis.get("config:prefixes"))
        self.owners = json.loads(self.db.redis.get("config:owners"))
        self.token = self.db.redis.get("config:token")

        commands.Bot.__init__(
            self,
            command_prefix=server_prefix,
            description=self.db.redis.get("config:description"),
            shard_count=int(self.db.redis.get("config:shard_count")),
            shard_id=shard_id,
            pm_help=True
        )

    async def on_ready(self):
        await self.wh.log("Logged in")
        await self.db.create_aioredis()
        self.loop.create_task(self.ticker())
        await self.reload_cogs()
        await self.wh.log("Ready!")
        self.ready = True

    async def on_server_join(self, server):
        try:
            _message = "Hello! Thanks for adding me to your server! For a list of commands, do `{0}help`. All commands start with my command prefix, `{0}`. For reference, to play music simply do `{0}play <something to search | url>`. Thanks for using Beemo! :)"
            await self.send_message(server.owner, _message.format(self.default_prefix[0]))
        except discord.errors.Forbidden:
            pass

        await self.wh.log("Joined **{0.name}** (`{0.id}`). I am now on {1} servers.".format(server, len(self.servers)))

    async def on_server_remove(self, server):
        await self.wh.log("Left **{0.name}** (`{0.id}`). I am now on {1} servers.".format(server, len(self.servers)))

    async def reload_cogs(self):
        await self.wh.log("Loading cogs")

        for cog in glob.glob(os.path.join(os.getcwd(), "cogs", "*.py")):
            import_name = cog.split(os.path.sep)[-1][:-3]

            if import_name != "__init__":
                import_name = "cogs."+import_name
                print("Loading "+import_name)

                try:
                    self.load_extension(import_name)
                except:
                    content = await paste(traceback.format_exc())
                    await self.wh.log("Failed to import {0}. {1}".format(import_name, content))
                    await self.wh.log("Restarting")
                    await self.logout()
                    break

        for cog in glob.glob(os.path.join(os.getcwd(), "cogs", "*", "__init__.py")):
            import_name = cog.split(os.path.sep)[-2]
            if import_name != "__init__":
                import_name = "cogs."+import_name
                print("Loading "+import_name)

                try:
                    self.load_extension(import_name)
                except:
                    content = await paste(traceback.format_exc())
                    await self.wh.log("Failed to import {0}. {1}".format(import_name, content))
                    await self.wh.log("Restarting")
                    await self.logout()
                    break

    def has_role(self, message, *roles):
        if message.server is None:
            return True

        if message.server.owner.id == message.author.id:
            return True

        for role in roles:
            if role in [x.name for x in message.author.roles]:
                return True

        return False

    async def on_message(self, message):
        async def _continue():
            await self.process_commands(message)

        if not self.ready:
            return

        if message.server is None:
            await _continue()
            return

        if message.author.id in self.owners:
            await _continue()
            return

        #check if the user has an access role

        access_role = await self.db.redis.get("server:{}:access_role".format(message.server.id))

        if access_role is not None:
            if not self.has_role(message, access_role):
                return

        #check if channel is disabled

        channel_disabled = await self.db.redis.get("server:{}:channel:{}:disabled".format(message.server.id, message.channel.id))
        if channel_disabled is not None:
            if not self.has_role(message, "Beemo Admin", "Beemo Music"):
                return

        await _continue()

    async def ticker(self):
        db = self.db.get_shard_storage()
        while True:
            try:
                voice_states = len([voice_state for channel_id, voice_state in self.cogs["Music"].voice_states.items() if voice_state.current is not None])
            except:
                voice_states = 0
            servers = 0
            users = 0
            channels = 0
            for server in self.servers:
                users += len(server.members)
                channels += len(server.channels)
                servers += 1

            await db.set("servers", servers, expire=20)
            await db.set("users", users, expire=20)
            await db.set("channels", channels, expire=20)
            await db.set("voice_states", voice_states, expire=20)

            await asyncio.sleep(10)

    #send_message modified to paste if the text is too big
    async def send_message(self, destination, content=None, *, tts=False, embed=None, transform_mentions=True):
        """|coro|
        Sends a message to the destination given with the content given.
        The destination could be a :class:`Channel`, :class:`PrivateChannel` or :class:`Server`.
        For convenience it could also be a :class:`User`. If it's a :class:`User` or :class:`PrivateChannel`
        then it sends the message via private message, otherwise it sends the message to the channel.
        If the destination is a :class:`Server` then it's equivalent to calling
        :attr:`Server.default_channel` and sending it there.
        If it is a :class:`Object` instance then it is assumed to be the
        destination ID. The destination ID is a *channel* so passing in a user
        ID will not be a valid destination.
        .. versionchanged:: 0.9.0
            ``str`` being allowed was removed and replaced with :class:`Object`.
        The content must be a type that can convert to a string through ``str(content)``.
        Parameters
        ------------
        destination
            The location to send the message.
        content
            The content of the message to send.
        tts : bool
            Indicates if the message should be sent using text-to-speech.
        Raises
        --------
        HTTPException
            Sending the message failed.
        Forbidden
            You do not have the proper permissions to send the message.
        NotFound
            The destination was not found and hence is invalid.
        InvalidArgument
            The destination parameter is invalid.
        Returns
        ---------
        :class:`Message`
            The message that was sent.
        """

        channel_id, guild_id = await self._resolve_destination(destination)


        if content:
            content = str(content)

            if len(content) > 2000:
                content = await paste(content)

            if transform_mentions:
                for key, value in _mentions_transforms.items():
                    content = content.replace(key, value)
        else:
            content = None

        if embed is not None:
            embed = embed.to_dict()


        data = await self.http.send_message(channel_id, content, guild_id=guild_id, tts=tts, embed=embed)
        channel = self.get_channel(data.get('channel_id'))
        message = self.connection._create_message(channel=channel, **data)
        return message

    async def has_tag(self, member, tag):
        tags = await self.db.redis.smembers("user:{0}:tags".format(member.id))
        return tag in tags
