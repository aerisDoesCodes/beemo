import discord

async def entry_to_code(bot, entries):
    width = max(map(lambda t: len(t[0]), entries))
    output = ['```']
    fmt = '{0:<{width}}: {1}'
    for name, entry in entries:
        output.append(fmt.format(name, entry, width=width))
    output.append('```')
    await bot.say('\n'.join(output))

async def indented_entry_to_code(bot, entries):
    width = max(map(lambda t: len(t[0]), entries))
    output = ['```']
    fmt = '\u200b{0:>{width}}: {1}'
    for name, entry in entries:
        output.append(fmt.format(name, entry, width=width))
    output.append('```')
    await bot.say('\n'.join(output))

async def describe_format(bot, entries):
    output = []
    fmt = "**{0}:** `{1}`"
    for name, entry in entries:
        output.append(fmt.format(name, entry))
    await bot.say('\n'.join(output))

async def set_format(bot, entries):
    output = []
    fmt = "**{0}:** `{1}` (set this with `set {2} [{0}]`)"
    for name, entry, commandname in entries:
        output.append(fmt.format(name, entry, commandname.lower()))
    await bot.say('\n'.join(output))

async def embed(bot, entries, thumbnail=None, author=None, **kwargs):
    data = discord.Embed(**kwargs)
    for entry in entries:
        data.add_field(name=entry[0], value=entry[1])

    if thumbnail is not None:
        data.set_thumbnail(url=thumbnail)

    if author is not None:
        data.set_author(name=author.name, icon_url=author.avatar_url)

    await bot.say(embed=data)


