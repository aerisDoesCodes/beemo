from discord.ext import commands
from util import checks


class Tag(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, aliases=["addtag", "stag"], no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def settag(self, ctx, *, info : str):
        """Sets a tag ="""
        name, value = info.split(" ", 1)
        name = name.lower()

        redis = self.bot.db.get_storage(ctx.message.server)

        await redis.set("tag:{0}".format(name), value)
        await self.bot.say("\N{OK HAND SIGN}")

    @commands.command(pass_context=True, aliases=["deletetag", "removetag", "rmtag", "rtag", "dtag"], no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def deltag(self, ctx, *, name : str):
        """Deletes a tag"""
        redis = self.bot.db.get_storage(ctx.message.server)

        name = name.lower()

        await redis.delete("tag:{0}".format(name))

    @commands.command(pass_context=True, aliases=["ltags"], no_pm=True)
    async def listtags(self, ctx):
        """Lists all the tags"""

        keys = []

        for key in await self.bot.db.redis.keys("server:{0}:tags:*".format(ctx.message.server)):
            key = key.lstrip("server:{0}:tags:*".format(ctx.message.server))
            keys.append(key)

        keys = ", ".join(keys)

        await self.bot.say("Keys:\n```{0}```".format(keys))

    @commands.command(pass_context=True, no_pm=True)
    async def tag(self, ctx, *, name : str):
        """Returns a tag."""
        redis = self.bot.db.get_storage(ctx.message.server)
        value = await redis.get("tag:{0}".format(name))
        if value is None:
            await self.bot.say("Tag not found.", transform_mentions=False)
        else:
            await self.bot.say(value)


def setup(bot):
    bot.add_cog(Tag(bot))
