from discord.ext import commands

import asyncio
import time
import datetime

STATUS_FORMAT = """Beemo Stats:


Uptime: **{0}**
Servers: **{1}**
Channels: **{2}**
Users: **{3}**
Shards: **{4}**
Voice States: **{5}**
Cached Searches: **{6}**
Database Operations: **{7}**
Database Operations per second: **{8}**
"""

class StatusUpdater(object):
    def __init__(self, bot):
        self.bot = bot
        self.uptime = time.time()
        self.bot.loop.create_task(self.ticker())

    async def ticker(self):
        self.statuschannel_id = await self.bot.db.redis.get("config:status_channel")
        self.statuschannel = self.bot.get_channel(self.statuschannel_id)

        if self.statuschannel is None:
            await self.bot.wh.log("Status channel is not present")
            return

        #first, remove all messages from the channel
        await self.bot.purge_from(self.statuschannel, limit=1000)

        #make inital message
        messageobj = await self.bot.send_message(self.statuschannel, "Initializing... please wait...")
        while True:
            #grab info
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

            #format message
            formatted_message = STATUS_FORMAT.format(
                uptime,
                servers,
                channels,
                users,
                self.bot.shard_count,
                voice_states,
                cached_searches,
                database_info["stats"]["total_commands_processed"],
                database_info["stats"]["instantaneous_ops_per_sec"]
            )
            #edit the message
            await self.bot.edit_message(messageobj, formatted_message)

            await asyncio.sleep(5)

def setup(bot):
    bot.add_cog(StatusUpdater(bot))
