import discord

def str2bool(v):
    return str(v).lower() in ("yes", "true", "t", "1")

class Entry(object):
    def __init__(self, player, req, requester=None, channel=None, voice_channel=None):
        self.requester = requester
        self.player = player
        self.req = req
        self.channel = channel
        self.voice_channel = voice_channel
    def __str__(self):
        if self.requester is None:
            fmt = '`{0.title}`'.format(self.player)
        else:
            fmt = '`{0.title}` (requested by `{1}`)'.format(self.player, self.requester.display_name)

        duration = self.player.duration
        if duration:
            fmt += " [`{0[0]}:{0[1]}`]".format(divmod(int(duration), 60))

        return fmt

    def get_embed(self, action=None):
        data = discord.Embed(
            title=self.player.title,
            colour=discord.Colour(0x2ecc71),
            description="[Help Beemo stay alive!](https://beemo.club)"
        )
        if action:
            data.add_field(name="Action", value=action)

        duration = self.player.duration
        if duration:
            data.add_field(name="Duration", value="{0[0]}m {0[1]}s".format(divmod(int(duration), 60)))

        if hasattr(self.player, "thumbnail"):
            data.set_thumbnail(url=self.player.thumbnail)

        if self.requester is not None:
            data.set_author(name=self.requester.display_name, icon_url=self.requester.avatar_url)

        if str2bool(self.player.is_live):
            data.add_field(name="Live?", value="Yes")

        #data.set_footer(text="Help Beemo stay alive: beemo.club")

        return data

class LiveEntry(object):
    def __str__(self):
        return "XenFM - XenFM.com"

    def get_embed(self, action=None):
        data = discord.Embed(
            title="XenFM - XenFM.com",
            colour=discord.Colour(0x2ecc71),
            url="https://xenfm.com",
            description="[Help Beemo stay alive!](https://beemo.club)"
        )

        if action:
            data.add_field(name="Action", value=action)

        data.add_field(name="Live?", value="Yes")
        data.set_footer(text="Beemo Autoplay Services")

        return data