import asyncio
import discord
import traceback
import copy

from .cache import generate_ytdl_player
from .entry import Entry, LiveEntry


def deepcopy(d):
    new_dict = {}
    for k,v in d.items():
        if isinstance(v, dict):
            new_dict[k] = deepcopy(v)
        else:
            new_dict[k] = v
    return new_dict

class State(object):
    opts = {
        'default_search': 'auto',
        'force_ipv4': True,
        'source_address': '0.0.0.0',
        "playlist_items": "0",
        "playlist_end": "0",
        "noplaylist": True
    }

    def __init__(self, cog, message):
        self.bot = cog.bot
        self.cog = cog
        self.server = message.server
        self.spawn_channel = message.channel
        self.redis = self.bot.db.get_storage(self.server)
        self.play_next_song = asyncio.Event()
        self.queue = asyncio.Queue(maxsize=15)
        self.voice = None
        self.current = None
        self.loop_started = False
        self.skip_votes = set()

    def start_loop(self):
        if not self.loop_started:
            self.loop_started = True
            self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False
        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing() and not isinstance(self.current, LiveEntry):
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def get_volume(self):
        volume = await self.redis.get("volume")
        if volume is None:
            volume = 0.6
        else:
            volume = float(volume)
            if volume == 0.6:
                await self.redis.delete("volume")

        return volume

    async def disconnect(self, message=False):
        if message:
            await self.bot.send_message(self.spawn_channel, "Queue concluded.")
            await self.bot.send_message(self.spawn_channel, "If you enjoy Beemo's music feature, please consider donating. Your donation will help us pay for Beemo's expensive servers. By donating, you also get a rank in Beemo's HQ, and loads more features listed at Beemo's HQ (+invite). https://beemo.club")
        if self.current is not None:
            try:
                self.current.player.stop()
            except:
                pass
        if self.voice is not None:
            try:
                await self.voice.disconnect()
            except:
                pass
        if self.loop_started:
            self.audio_player.cancel()
        if self.server.id in self.cog.voice_states.keys():
            del self.cog.voice_states[self.server.id]

    async def audio_player_task(self):
        while self.voice is None:
            await asyncio.sleep(.1)

        while True:
            self.play_next_song.clear()
            self.current = None

            if self.queue.empty():
                if await self.bot.has_tag(self.server.owner, "donator"):
                    while self.queue.empty():
                        await asyncio.sleep(3)
                        #play some radio here
                        self.current = LiveEntry()

                        self.current.player = self.voice.create_ffmpeg_player("http://82.199.155.35:8000/stream")
                        self.current.player.volume = await self.get_volume()
                        self.current.player.start()

                        while self.queue.empty() and not self.current.player.is_done():
                            await asyncio.sleep(.1)

                        self.current.player.stop()
                        self.current = None
                else:
                    await self.disconnect(message=True)
                    break

            if 1 >= len(self.voice.channel.voice_members):
                await self.disconnect(message=True)
                break

            self.current = await self.queue.get()

            self.voice.encoder.set_fec(False)
            self.voice.encoder.set_bitrate(64)

            #Play (where self.current is a State object)

            try:
                await self.voice.move_to(self.current.voice_channel)
            except discord.errors.InvalidArgument:
                pass
            except:
                traceback.print_exc()

            self.spawn_channel = self.current.channel
            embed = self.current.get_embed(action="Now Playing")

            try:
                await self.bot.send_message(self.current.channel, embed=embed)
            except discord.Forbidden:
                pass

            self.current.player.start()
            self.current.player.volume = await self.get_volume()

            await self.play_next_song.wait()

    async def play(self, url, voice_channel, ctx):
        try:
            player = await generate_ytdl_player(self, url, ytdl_options=self.opts, after=self.toggle_next)
            entry = Entry(player, url, channel=ctx.message.channel, requester=ctx.message.author, voice_channel=voice_channel)
            return entry
        except:
            traceback.print_exc()
            return False


