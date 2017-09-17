from discord.ext import commands
from util import checks

import discord

class Admin(object):
    def __init__(self, bot):
        self.bot = bot
        self.muted_role = "BeemoMuted"

    async def add_case(self, user, server, type):
        await self.bot.cogs["ModLog"].add_case(user, server, type)

    @commands.command(pass_context=True, no_pm=True, aliases=["clear"])
    @checks.admin_or_permissions(manage_messages=True)
    async def clean(self, ctx, *, limit : int = 100, user_to_purge : discord.Member = None):
        """Clean channel messages."""
        def check(m):
            if user_to_purge is not None:
                return m.author.id == user_to_purge.id
            return True

        try:
            deleted = await self.bot.purge_from(ctx.message.channel, limit=limit, check=check)
            await self.bot.say("Deleted {0} message(s)".format(len(deleted)))
        except discord.Forbidden:
            await self.bot.say("I don't have permission to manage messages.")

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(mute_members=True)
    async def mute(self, user : discord.Member):
        """Mutes a user."""
        role = discord.utils.get(user.server.roles, name=self.muted_role)
        if not role:
            try:
                role = await self.bot.create_role(user.server, name=self.muted_role, permissions=discord.Permissions.none())

                try:
                    for c in user.server.channels:
                        await self.channel_setup(c, role)
                except discord.Forbidden:
                    await self.bot.say("An error occured while setting channel permissions, Please check your channel permissions for the {0} role.".format(self.muted_role))
            except discord.Forbidden:
                await self.bot.say("I do not have the `Manage Roles` permission.")
                return

        try:
            await self.bot.add_roles(user, role)
            await self.bot.say("\N{OK HAND SIGN}")
            #add to mod log
        except discord.Forbidden:
            await self.bot.say("I don't have permission to modify roles.")

        await self.add_case(user, user.server, "MUTE")

    @commands.command(no_pm=True, aliases=["umute"])
    @checks.admin_or_permissions(mute_members=True)
    async def unmute(self, user : discord.Member):
        """Unmutes a user."""
        role = discord.utils.get(user.server.roles, name=self.muted_role)

        if not role:
            await self.bot.say("There isn't even a muted role")
            return

        try:
            await self.bot.remove_roles(user, role)
            await self.bot.say("\N{OK HAND SIGN}")
        except discord.Forbidden:
            await self.bot.say("I don't have permission to modify roles.")

        await self.add_case(user, user.server, "UNMUTE")

    async def on_channel_create(self, channel):
        try:
            r = discord.utils.get(channel.server.roles, name=self.muted_role)
            if r:
                await self.channel_setup(channel, r)
        except:
            pass
    @commands.command(no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def ban(self, user : discord.Member, delete_message_days : int = 1):
        """Bans a user."""
        try:
            await self.bot.ban(user, delete_message_days=delete_message_days)
            await self.bot.say("\N{OK HAND SIGN}")
        except discord.Forbidden:
            await self.bot.say("I don't have permission to ban members")

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def unban(self, user : discord.Member):
        """Unbans a user."""
        try:
            await self.bot.unban(user)
            await self.bot.say("\N{OK HAND SIGN}")
        except discord.Forbidden:
            await self.bot.say("I don't have permission to unban members")

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(kick_members=True)
    async def kick(self, user : discord.Member):
        """Kicks a user."""
        try:
            await self.bot.kick(user)
            await self.bot.say("\N{OK HAND SIGN}")
        except discord.Forbidden:
            await self.bot.say("I don't have permission to kick members")

        await self.add_case(user, user.server, "KICK")

    @commands.command(no_pm=True, aliases=["sban"])
    @checks.admin_or_permissions(kick_members=True)
    async def softban(self, user : discord.Member):
        """Softbans a user (Ban&Unban)"""
        try:
            await self.bot.ban(user, delete_message_days=7)
            await self.bot.unban(user.server, user)
            await self.bot.say("\N{OK HAND SIGN}")
        except discord.Forbidden:
            await self.bot.say("I don't have permission to ban members")

    @commands.command(no_pm=True, aliases=["vkick"])
    @checks.admin_or_permissions(kick_members=True)
    async def vckick(self, user : discord.Member):
        """Kicks a user from a voice channel."""
        try:
            channel = await self.bot.create_channel(user.server, 'beemo vckick', type=discord.ChannelType.voice)
        except discord.Forbidden:
            await self.bot.say("I don't have permission to create channels.")
            return

        try:
            await self.bot.move_member(user, channel)
        except discord.Forbidden:
            await self.bot.say("I don't have permission to move members.")

        await self.bot.delete_channel(channel)
        await self.bot.say("\N{OK HAND SIGN}")
        await self.add_case(user, user.server, "VOICE KICK")

    @commands.command(no_pm=True, pass_context=True, aliases=["ginvite", "cinvite", "generateinvite"])
    @checks.admin_or_permissions(create_instant_invite=True)
    async def createinvite(self, ctx, max_age : int = 0, max_uses : int = 0, temporary : bool = False):
        """Generates a instant invite"""
        try:
            invite = await self.bot.create_invite(ctx.message.server, max_age=max_age, max_uses=max_uses, temporary=temporary)
            await self.bot.say(invite.url)
        except discord.Forbidden:
            await self.bot.say("I don't have permission to create invites.")

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def role(self, ctx):
        """Role administration commands."""
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid command.")

    @role.command(aliases=["give", "add"])
    async def grant(self, member : discord.Member, *, role : discord.Role):
        """Gives a user a role."""
        try:
            await self.bot.add_roles(member, role)
            await self.bot.say("\N{OK HAND SIGN}")
        except discord.Forbidden:
            await self.bot.say("I don't have permission to manage roles.")

    @role.command(aliases=["remove", "deny"])
    async def take(self, member : discord.Member, *, role : discord.Role):
        """Removes a role from a user."""
        try:
            await self.bot.remove_roles(member, role)
            await self.bot.say("\N{OK HAND SIGN}")
        except discord.Forbidden:
            await self.bot.say("I don't have permission to manage roles.")




    async def channel_setup(self, c, role):
        perms = discord.PermissionOverwrite()

        if c.type == discord.ChannelType.text:
            perms.send_messages = False
            perms.send_tts_messages = False

        elif c.type == discord.ChannelType.voice:
            perms.speak = False

        await self.bot.edit_channel_permissions(c, role, perms)


def setup(bot):
    bot.add_cog(Admin(bot))

