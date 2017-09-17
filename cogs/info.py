from discord.ext import commands
from util import formats
from collections import Counter


import discord
import copy

class Info(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True, aliases=["uinfo", "whoami"])
    async def userinfo(self, ctx, *, member : discord.Member = None):
        """Shows info about a member."""
        channel = ctx.message.channel
        if member is None:
            member = ctx.message.author

        roles = [role.name.replace('@', '@\u200b') for role in member.roles]
        shared = sum(1 for m in self.bot.get_all_members() if m.id == member.id)
        voice = member.voice_channel
        if voice is not None:
            other_people = len(voice.voice_members) - 1
            voice_fmt = '{} with {} others' if other_people else '{} by themselves'
            voice = voice_fmt.format(voice.name, other_people)
        else:
            voice = 'Not connected.'

        internal_tags = ", ".join(await self.bot.db.redis.smembers("user:{0}:tags".format(member.id)))

        entries = [
            ('Name', member.name),
            ('Tag', member.discriminator),
            ('ID', member.id),
            ('Internal Tags', internal_tags),
            ('Joined', member.joined_at),
            ('Created', member.created_at),
            ('Roles', ', '.join(roles)),
            ('Servers', '{} shared'.format(shared)),
            ('Voice', voice),
        ]

        await formats.embed(self.bot, entries, colour=member.top_role.colour, author=member, thumbnail=member.avatar_url)

    @commands.command(pass_context=True, no_pm=True, aliases=["sinfo"])
    async def serverinfo(self, ctx):
        """Shows info about the server."""
        server = ctx.message.server
        roles = [role.name.replace('@', '@\u200b') for role in server.roles]

        secret_member = copy.copy(server.me)
        secret_member.id = '0'
        secret_member.roles = [server.default_role]

        # figure out what channels are 'secret'
        secret_channels = 0
        secret_voice = 0
        text_channels = 0
        for channel in server.channels:
            perms = channel.permissions_for(secret_member)
            is_text = channel.type == discord.ChannelType.text
            text_channels += is_text
            if is_text and not perms.read_messages:
                secret_channels += 1
            elif not is_text and (not perms.connect or not perms.speak):
                secret_voice += 1

        regular_channels = len(server.channels) - secret_channels
        voice_channels = len(server.channels) - text_channels
        member_by_status = Counter(str(m.status) for m in server.members)
        member_fmt = '{0} ({1[online]} online, {1[idle]} idle, {1[offline]} offline)'
        channels_fmt = '{} Text ({} secret) / {} Voice ({} locked)'
        channels = channels_fmt.format(text_channels, secret_channels, voice_channels, secret_voice)

        entries = [
            ('Name', server.name),
            ('ID', server.id),
            ('Channels', channels),
            ('Created', server.created_at),
            ('Members', member_fmt.format(len(server.members), member_by_status)),
            ('Owner', server.owner),
            ('Roles', ', '.join(roles)),
        ]

        await formats.embed(self.bot, entries, title=server.name, author=server.owner, thumbnail=server.icon_url, colour=discord.Colour(0x2ecc71))

    @commands.command(pass_context=True, aliases=["confirm"], hidden=True)
    async def verify(self, ctx, *, member : discord.Member = None):
        if member is None:
            member = ctx.message.author

        tags = await self.bot.db.redis.smembers("user:{0}:tags".format(member.id))

        verify_tag = None

        if "helper" in tags:
            verify_tag = "Helper"

        if "mod" in tags:
            verify_tag = "Moderator"

        if "owner" in tags:
            verify_tag = "owner"

        if verify_tag is not None:
            await self.bot.say("{0} is a {1} at Beemo's HQ.".format(member.mention, verify_tag))

def setup(bot):
    bot.add_cog(Info(bot))