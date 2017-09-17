from discord.ext import commands
from util import checks

class Autoplay(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(no_pm=True, pass_context=True, aliases=["radio"], invoke_without_command=True)
    @checks.admin_or_permissions(manage_server=True)
    async def autoplay(self, ctx):
        """Autoplay commands. See 'help autoplay'"""
        if not await self.bot.has_tag(ctx.message.server.owner, "donator"):
            raise checks.PermissionError('This is not a donator-enabled server.')
            return

        if ctx.invoked_subcommand is None:
            await self.bot.say('Invalid git command passed...')

    @autoplay.command(pass_context=True)
    async def list(self, ctx):
        """Lists the songs in the autoplay"""
        redis = self.bot.db.get_storage(ctx.message.server)
        contents = await redis.smembers("autoplay")

        if contents == []:
            await self.bot.say("Autoplay is empty. You can add music by doing `autoplay add <url|search>`")
        else:
            message = "Autoplay list:\n\n"

            for url in contents:
                message += "- {0}".format(url)

            await self.bot.say(message)

    @autoplay.command(pass_context=True)
    async def add(self, ctx, *, url : str):
        """Adds a song to the autoplay"""

        redis = self.bot.db.get_storage(ctx.message.server)
        contents = await redis.sadd("autoplay", url)

        await self.bot.say("\N{OK HAND SIGN}")

    @autoplay.command(pass_context=True, aliases=["del", "delete"])
    async def remove(self, ctx, *, url : str):
        """Adds a song to the autoplay"""

        redis = self.bot.db.get_storage(ctx.message.server)
        contents = await redis.srem("autoplay", url)

        await self.bot.say("\N{OK HAND SIGN}")


def setup(bot):
    bot.add_cog(Autoplay(bot))