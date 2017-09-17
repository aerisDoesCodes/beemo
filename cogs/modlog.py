from discord.ext import commands
from util import checks

import discord

NEW_CASE_FORMAT = """**{0}** | Case {1}
**User**: {2}
**Reason**: Set this with `beemo reason {1} <reason>`
"""

CASE_FORMAT = """**{0}** | Case {1}
**User**: {2}
**Reason**: {3}
**Responsible Moderator**: {4}
"""

class ModLog(object):
    def __init__(self, bot):
        self.bot = bot

    async def get_new_case_id(self, server):
        keys = await self.bot.db.redis.keys("server:{0}:mod-log:case:*:message".format(server.id))

        return len(keys)+1

    async def add_case(self, user, server, type):
        redis = self.bot.db.get_storage(server)
        modlog_channel = await redis.get("modlogchannel")
        modlog_channel = server.get_channel(modlog_channel)

        if modlog_channel is None:

            modlog_channel = discord.utils.get(server.channels, name="beemo-mod-log")
            if modlog_channel is None:
                return

        case_id = await self.get_new_case_id(server)

        #send message
        formatted_message = NEW_CASE_FORMAT.format(type, case_id, user)
        message_object = await self.bot.send_message(modlog_channel, formatted_message)

        #remember the id

        await redis.set("mod-log:case:{0}:message".format(case_id), message_object.id)
        await redis.set("mod-log:case:{0}:user".format(case_id), str(user))
        await redis.set("mod-log:case:{0}:type".format(case_id), type)

    async def on_member_ban(self, member):
        await self.add_case(member, member.server, "BAN")

    async def on_member_unban(self, server, user):
        await self.add_case(user, server, "UNBAN")

    @commands.command(pass_context=True, no_pm=True, aliases=["r"], name="reason")
    @checks.admin_or_permissions(ban_members=True)
    async def _reason(self, ctx, case, *, reason : str):
        """Add a reason for a ban/unban"""
        if case == "l":
            case = len(await self.bot.db.redis.keys("server:{0}:mod-log:case:*:message".format(ctx.message.server.id)))
        else:
            case = int(case)
        redis = self.bot.db.get_storage(ctx.message.server)
        message_id = await redis.get("mod-log:case:{0}:message".format(case))
        user = await redis.get("mod-log:case:{0}:user".format(case))
        _type = await redis.get("mod-log:case:{0}:type".format(case))

        if user is None:
            await self.bot.say("Case not found.")
            return

        #reformat
        formatted_message = CASE_FORMAT.format(_type, case, user, reason, ctx.message.author)

        #get mod log channel first
        modlog_channel = await redis.get("modlogchannel")
        modlog_channel = ctx.message.server.get_channel(modlog_channel)

        if modlog_channel is None:

            modlog_channel = discord.utils.get(ctx.message.server.channels, name="beemo-mod-log")
            if modlog_channel is None:
                await self.bot.say("Moderator log channel not found.")

        #find original message
        case_message = await self.bot.get_message(modlog_channel, message_id)
        if case_message is None:
            await self.bot.say("Original message not found.")
            return

        await self.bot.edit_message(case_message, formatted_message)
        await self.bot.say("\N{OK HAND SIGN}")






def setup(bot):
    bot.add_cog(ModLog(bot))