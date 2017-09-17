from discord.ext import commands
from util import checks


import aiohttp
import discord

class Owner(object):
    def __init__(self, bot):
        self.bot = bot
        self.aiosession = aiohttp.ClientSession(loop=self.bot.loop)

    @commands.group(pass_context=True, hidden=True)
    @checks.is_owner()
    async def owner(self, ctx):
        """Bot owner commands"""
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid command.")

    @owner.command(pass_context=True)
    async def setavatar(self, ctx, *, url : str):
        thing = url.strip('<>')
        with aiohttp.Timeout(10):
            async with self.aiosession.get(thing) as res:
                await self.bot.edit_profile(avatar=await res.read())

    @owner.command(name="reload")
    async def _reload(self, *, module : str):
        """Reloads a module"""
        self.bot.unload_extension(module)
        self.bot.load_extension(module)
        await self.bot.say("\N{OK HAND SIGN}")

    @owner.command()
    async def load(self, *, module : str):
        """Loads a module"""
        self.bot.load_extension(module)
        await self.bot.say("\N{OK HAND SIGN}")

    @owner.command()
    async def unload(self, *, module : str):
        """Unloads a module"""
        self.bot.unload_extension(module)
        await self.bot.say("\N{OK HAND SIGN}")

    @owner.group(pass_context=True)
    async def tags(self, ctx):
        """User tags (for setting internal ranks)"""
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid commmand.")

    @tags.command()
    async def add(self, member : discord.Member, tag : str):
        await self.bot.db.redis.sadd("user:{0}:tags".format(member.id), tag)
        await self.bot.say("\N{OK HAND SIGN}")


    @tags.command()
    async def list(self, member : discord.Member):
        _tags = await self.bot.db.redis.smembers("user:{0}:tags".format(member.id))

        _message = "**{0}** tag(s):\n\n{1}".format(len(_tags), "\n".join(_tags))

        await self.bot.say(_message)

    @tags.command()
    async def delete(self, member : discord.Member, tag : str):
        await self.bot.db.redis.srem("user:{0}:tags".format(member.id), tag)
        await self.bot.say("\N{OK HAND SIGN}")




def setup(bot):
    bot.add_cog(Owner(bot))