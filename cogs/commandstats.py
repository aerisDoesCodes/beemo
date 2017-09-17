import operator
from util import formats
from discord.ext import commands

class CommandStats(object):
    def __init__(self, bot):
        self.bot = bot

    async def on_command(self, command, ctx):
        if command.name not in await self.bot.db.redis.hkeys("stats:commands_used"):
            await self.bot.db.redis.hset("stats:commands_used", command.name, 0)

        current = int(await self.bot.db.redis.hget("stats:commands_used", command.name))
        await self.bot.db.redis.hset("stats:commands_used", command.name, current+1)

    @commands.command(hidden=True, aliases=["cstats"])
    async def commandstats(self):
        commands_used = await self.bot.db.redis.hgetall("stats:commands_used")
        commands_used = {k: int(v) for k,v in commands_used.items()}
        commands_used = sorted(commands_used.items(), key=operator.itemgetter(1), reverse=True)

        await formats.indented_entry_to_code(self.bot, commands_used)

def setup(bot):
    bot.add_cog(CommandStats(bot))