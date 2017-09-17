from discord.ext import commands
from util import checks, formats

import discord

class Settings(object):
    def __init__(self, bot):
        self.bot = bot

    def format_greeting(self, member, greeting_message):
        greeting_message = greeting_message.replace("%mention%", member.mention)
        greeting_message = greeting_message.replace("%server%", member.server.name)
        return greeting_message

    def format_farewell(self, member, farewell_message):
        farewell_message = farewell_message.replace("%mention%", str(member))
        farewell_message = farewell_message.replace("%server%", member.server.name)
        return farewell_message

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_server=True)
    async def channeltoggle(self, ctx):
        """Enables or disables commands for the current channel. Those with the Beemo Admin/Music can do this."""
        redis = self.bot.db.get_storage(ctx.message.server)

        current_setting = await redis.get("channel:{0}:disabled".format(ctx.message.channel.id))

        #True == disabled
        #False == enabled

        if current_setting == "True":
            #Disable commands
            await redis.delete("channel:{0}:disabled".format(ctx.message.channel.id))

            await self.bot.say("Enabled commands for this channel.")
        else:
            await redis.set("channel:{0}:disabled".format(ctx.message.channel.id), "True")

            await self.bot.say("Disabled commands for this channel.")

    @commands.group(pass_context=True, no_pm=True, name="set")
    @checks.admin_or_permissions(manage_server=True)
    async def _set(self, ctx):
        """Set server settings"""
        if ctx.invoked_subcommand is None:
            redis = self.bot.db.get_storage(ctx.message.server)

            prefix = await redis.get("prefix")
            if prefix is None:
                prefix = self.bot.default_prefix[0]+" (default)"

            music_channel = await redis.get("musicchannel")
            if music_channel is None:
                music_channel = "Any (default)"
            else:
                music_channel = ctx.message.server.get_channel(music_channel).name

            log_channel = await redis.get("logchannel")
            if log_channel is None:
                log_channel = "None (default)"
            else:
                log_channel = ctx.message.server.get_channel(log_channel).name

            modlog_channel = await redis.get("modlogchannel")
            if modlog_channel is None:
                modlog_channel = "#beemo-mod-log (default)"
            else:
                modlog_channel = ctx.message.server.get_channel(modlog_channel).name

            access_role = await redis.get("access_role")
            if access_role is None:
                access_role = "Any (default)"

            greeting_message = await redis.get("greeting_message")
            if greeting_message is None:
                greeting_message = "None (default)"

            greeting_in_dm = await redis.get("greeting_in_dm")
            if greeting_in_dm is None:
                greeting_in_dm = "No (default)"

            farewell_message = await redis.get("farewell_message")
            if farewell_message is None:
                farewell_message = "None (default)"

            nsfw_role = await redis.get("nsfw_role")
            if nsfw_role is None:
                nsfw_role = "Beemo NSFW (default)"

            mentionspam_count = await redis.get("mentionspam_count")
            if mentionspam_count is None:
                mentionspam_count = "Disabled (default)"

            entries = [
                ("Prefix", prefix, "Prefix"),
                ("Music Channel", music_channel, "musicchannel"),
                ("Log Channel", log_channel, "logchannel"),
                ("Moderator Log Channel", modlog_channel, "modlogchannel"),
                ("Access role", access_role, "accessrole"),
                ("NSFW role", nsfw_role, "nsfwrole"),
                ("Greeting", greeting_message, "greeting"),
                ("Send greeting in DM", greeting_in_dm, "greetingindm"),
                ("Farewell", farewell_message, "farewell"),
                ("Mentionspam (minimum mentions)", mentionspam_count, "mentionspamcount")
            ]

            await formats.set_format(self.bot, entries)

    @_set.command(pass_context=True, name="prefix")
    async def _prefix(self, ctx, *, prefix : str = None):
        """Set prefix"""
        redis = self.bot.db.get_storage(ctx.message.server)
        if prefix is None:
            await redis.delete("prefix")
            await self.bot.say("Cleared the prefix")
            return

        await redis.set("prefix", prefix)
        await self.bot.say("Set the prefix to `{0}`.".format(prefix))

    @_set.command(pass_context=True)
    async def musicchannel(self, ctx, channel : discord.Channel = None):
        """Sets the music channel"""
        redis = self.bot.db.get_storage(ctx.message.server)
        if channel is None:
            await redis.delete("musicchannel")
            await self.bot.say("Cleared the music channel.")
            return

        await redis.set("musicchannel", channel.id)
        await self.bot.say("Set the music channel to `{0.name}` (`{0.id}`)".format(channel))

    @_set.command(pass_context=True)
    async def logchannel(self, ctx, channel : discord.Channel = None):
        """Sets the log channel"""
        redis = self.bot.db.get_storage(ctx.message.server)
        if channel is None:
            await redis.delete("logchannel")
            await self.bot.say("Cleared the log channel.")
            return

        await redis.set("logchannel", channel.id)
        await self.bot.say("Set the log channel to `{0.name}` (`{0.id}`)".format(channel))

    @_set.command(pass_context=True)
    async def modlogchannel(self, ctx, channel : discord.Channel = None):
        """Sets the moderator log channel"""
        redis = self.bot.db.get_storage(ctx.message.server)
        if channel is None:
            await redis.delete("modlogchannel")
            await self.bot.say("Cleared the moderator log channel.")
            return

        await redis.set("modlogchannel", channel.id)
        await self.bot.say("Set the moderator log channel to `{0.name}` (`{0.id}`)".format(channel))


    @_set.command(pass_context=True)
    async def accessrole(self, ctx, *, role : discord.Role = None):
        redis = self.bot.db.get_storage(ctx.message.server)
        if role is None:
            await redis.delete("access_role")
            await self.bot.say("Deleted the access role.")
            return

        await redis.set("access_role", role.name)
        await self.bot.say("Set the access role to `{0.name}` (`{0.id}`)".format(role))

    @_set.command(pass_context=True)
    async def nsfwrole(self, ctx, *, role : discord.Role = None):
        redis = self.bot.db.get_storage(ctx.message.server)
        if role is None:
            await redis.delete("nsfw_role")
            await self.bot.say("Deleted the NSFW role.")
            return

        await redis.set("nsfw_role", role.name)
        await self.bot.say("Set the NSFW role to `{0.name}` (`{0.id}`)".format(role))

    @_set.command(pass_context=True)
    async def greeting(self, ctx, *, greeting_message : str = None):
        redis = self.bot.db.get_storage(ctx.message.server)

        if greeting_message is None:
            await redis.delete("greeting_message")
            await self.bot.say("Deleted the greeting.")
            return

        await redis.set("greeting_message", greeting_message)
        greeting_message = self.format_greeting(ctx.message.author, greeting_message)
        await self.bot.say("Set the greeting to `{}` (formatted example).".format(greeting_message))

    @_set.command(pass_context=True)
    async def greetingindm(self, ctx, *, greeting_in_dm : bool = None):
        redis = self.bot.db.get_storage(ctx.message.server)
        if greeting_in_dm is None or greeting_in_dm is False:
            await redis.delete("greeting_in_dm")
            await self.bot.say("Set the greeting target to the default channel.")
            return

        await redis.set("greeting_in_dm", "True")
        await self.bot.say("Set the greeting target to direct message.")


    async def on_member_join(self, member):
        redis = self.bot.db.get_storage(member.server)
        greeting_message = await redis.get("greeting_message")

        if greeting_message is not None:
            greeting_message = self.format_greeting(member, greeting_message)

            greeting_in_dm = await redis.get("greeting_in_dm")
            if greeting_in_dm is not None:
                channel = member
            else:
                channel = member.server.default_channel

            await self.bot.send_message(channel, greeting_message, transform_mentions=False)

        log_channel = await redis.get("logchannel")
        if log_channel is not None:
            log_channel = member.server.get_channel(log_channel)

            if log_channel is None:
                await redis.delete("logchannel")
                return

            await self.bot.send_message(log_channel, "{0} has joined the guild.".format(member))

    @_set.command(pass_context=True)
    async def farewell(self, ctx, *, farewell_message : str = None):
        redis = self.bot.db.get_storage(ctx.message.server)

        if farewell_message is None:
            await redis.delete("farewell_message")
            await self.bot.say("Deleted the farewell.")
            return

        await redis.set("farewell_message", farewell_message)
        farewell_message = self.format_farewell(ctx.message.author, farewell_message)
        await self.bot.say("Set the farewell to `{}` (formatted example).".format(farewell_message))

    @_set.command(pass_context=True)
    async def mentionspamcount(self, ctx, *, mentionspam_count : int = None):
        redis = self.bot.db.get_storage(ctx.message.server)
        if mentionspam_count is None or mentionspam_count == 0:
            await redis.delete("mentionspam_count")
            await self.bot.say("Disabled mention spam banning.")
            return

        await redis.set("mentionspam_count", mentionspam_count)
        await self.bot.say("Set the mention spam minimum to `{0}` mentions".format(mentionspam_count))

    async def on_member_remove(self, member):
        redis = self.bot.db.get_storage(member.server)
        farewell_message = await redis.get("farewell_message")

        if farewell_message is not None:
            farewell_message = self.format_farewell(member, farewell_message)

            await self.bot.send_message(member.server.default_channel, farewell_message)

        log_channel = await redis.get("logchannel")
        if log_channel is not None:
            log_channel = member.server.get_channel(log_channel)

            if log_channel is None:
                await redis.delete("logchannel")
                return

            await self.bot.send_message(log_channel, "{0} has left the guild.".format(member))






def setup(bot):
    bot.add_cog(Settings(bot))