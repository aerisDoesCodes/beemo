from discord.ext import commands

class MentionSpam(object):
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        if message.server is None:
            return

        redis = self.bot.db.get_storage(message.server)

        mention_count = await redis.get("mentionspam_count")

        if mention_count is not None:
            if len(message.mentions) >= int(mention_count):
                #ban the user
                await self.bot.ban(message.author, delete_message_days=7)
                await self.bot.send_message(message.channel, "Banned {0} for spamming.".format(message.author))

def setup(bot):
    bot.add_cog(MentionSpam(bot))