from discord.ext import commands
from util import checks

import discord

class Autorole(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, aliases=["arole"])
    @checks.admin_or_permissions(manage_roles=True)
    async def autorole(self, ctx):
        """Autorole (Join and Get)

Examples:
autorole add join Role name
autorole remove join Role name
autorole add get Role name (users can do -getrole to get this role)
autorole remove get Role name
autorole add bot Role name (Bots will get this role when they join)
"""
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid command.")

    @autorole.group(pass_context=True)
    async def add(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid command.")

    @autorole.group(pass_context=True, aliases=["remove", "take", "del"])
    async def delete(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid command.")

    #AUTOROLE (JOIN)

    @add.group(pass_context=True, name="join")
    async def add_join(self, ctx, *, role : discord.Role):
        redis = self.bot.db.get_storage(ctx.message.server)

        await redis.sadd("autorole:join", role.id)
        await self.bot.say("\N{OK HAND SIGN}")

    @delete.group(pass_context=True, name="join")
    async def delete_join(self, ctx, *, role : discord.Role):
        redis = self.bot.db.get_storage(ctx.message.server)

        await redis.srem("autorole:join", role.id)
        await self.bot.say("\N{OK HAND SIGN}")

    async def on_member_join(self, member):
        redis = self.bot.db.get_storage(member.server)
        autojoin_role_ids = await redis.smembers("autorole:join")
        if member.bot:
            bot_role_ids = await redis.smembers("autorole:bot")
            autojoin_role_ids = autojoin_role_ids + bot_role_ids
        autojoin_roles = []

        for role_id in autojoin_role_ids:
            r = discord.utils.get(member.server.roles, id=role_id)
            if r:
                autojoin_roles.append(r)

        if autojoin_roles == []:
            return

        try:
            await self.bot.add_roles(member, *autojoin_roles)
        except discord.Forbidden:
            await self.bot.send_message(member.server.owner, "I was unable to give user {0} the autojoin role when the user joined {1}, do I have the Manage Roles permission?".format(member, member.server.name))

        #autorole (bot)


    #AUTOROLE (GET)

    @add.group(pass_context=True, name="get")
    async def add_get(self, ctx, *, role : discord.Role):
        redis = self.bot.db.get_storage(ctx.message.server)

        await redis.sadd("autorole:get", role.id)
        await self.bot.say("\N{OK HAND SIGN}")

    @delete.group(pass_context=True, name="get")
    async def delete_get(self, ctx, *, role : discord.Role):
        redis = self.bot.db.get_storage(ctx.message.server)

        await redis.srem("autorole:get", role.id)
        await self.bot.say("\N{OK HAND SIGN}")

    @commands.command(pass_context=True)
    async def getrole(self, ctx, *, role : discord.Role):
        redis = self.bot.db.get_storage(ctx.message.server)

        if role.id in await redis.smembers("autorole:get"):
            try:
                await self.bot.add_roles(ctx.message.author, role)
                await self.bot.say("\N{OK HAND SIGN}")
            except discord.Forbidden:
                await self.bot.say("I don't have permission to give roles.")
        else:
            await self.bot.say("That role is not in the autorole list, owners can add it using `autorole add get {0}`".format(role.name))

    #AUTOROLE (BOT)

    @add.group(pass_context=True, name="bot")
    async def add_bot(self, ctx, *, role : discord.Role):
        redis = self.bot.db.get_storage(ctx.message.server)

        await redis.sadd("autorole:bot", role.id)
        await self.bot.say("\N{OK HAND SIGN}")

    @delete.group(pass_context=True, name="bot")
    async def delete_bot(self, ctx, *, role : discord.Role):
        redis = self.bot.db.get_storage(ctx.message.server)

        await redis.srem("autorole:bot", role.id)
        await self.bot.say("\N{OK HAND SIGN}")



def setup(bot):
    bot.add_cog(Autorole(bot))