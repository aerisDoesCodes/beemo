from discord.ext import commands

async def server_prefix(bot, message):
	if message.server is None:
		return commands.when_mentioned_or(*bot.default_prefix+[""])(bot, message)

	server_prefix = await bot.db.redis.get("server:{0}:prefix".format(message.server.id))
	if server_prefix is not None:
		return commands.when_mentioned_or(server_prefix)(bot, message)

	return commands.when_mentioned_or(*bot.default_prefix)(bot, message)