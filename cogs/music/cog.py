from discord.ext import commands
from util import checks
from .state import State

import discord
import traceback

def str2bool(v):
    return str(v).lower() in ("yes", "true", "t", "1")

class Music(object):
    def __init__(self, bot):
        self.bot = bot

        self.voice_states = {}

    def get_voice_state(self, message):
        state = self.voice_states.get(message.server.id)
        if state is None:
            state = State(self, message)
            self.voice_states[message.server.id] = state

        return state


    @commands.command(no_pm=True, pass_context=True)
    async def play(self, ctx, *, url : str):
        """Play music."""
        state = self.get_voice_state(ctx.message)

        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say("You are not in a voice channel.")
            return

        if state.queue.full() and not await self.bot.has_tag(ctx.message.author, "donator"):
            await self.bot.say("The queue is currently full.")
            return

        redis = self.bot.db.get_storage(ctx.message.server)
        musicchannel = await redis.get("musicchannel")
        if musicchannel is not None:
            if ctx.message.author.voice_channel.id != musicchannel:
                musicchannelobj = discord.utils.get(ctx.message.server.channels, id=musicchannel)
                if musicchannelobj is not None:
                    await self.bot.say("You must be in the music channel **{0}** to use the bot.".format(musicchannelobj.name))
                    return
                else:
                    await redis.delete("musicchannel")

        state = self.get_voice_state(ctx.message)

        summon_message = await self.bot.say("Attempting to join the voice channel.")
        try:
            if state.voice is None:
                state.voice = await self.bot.join_voice_channel(summoned_channel)
        except discord.errors.ClientException:
            #Bot is already in voice channel
            state.voice = self.bot.voice_client_in(ctx.message.server)
            if state.voice is None:
                #shit
                await self.bot.edit_message(summon_message, "Unable to join the voice channel.")
                return
        except:
            #traceback.print_exc()
            await self.bot.edit_message(summon_message, "Unable to join the voice channel.")
            return
        await self.bot.edit_message(summon_message, "Joined the voice channel")

        entry = await state.play(url, summoned_channel, ctx)

        if entry == False or entry is None:
            await self.bot.edit_message(summon_message, "Unable to play.")
            return

        if int(entry.player.duration) > 3600 and not await self.bot.has_tag(ctx.message.author, "donator"):
            await self.bot.edit_message(summon_message, "Video is too long.")
            return

        if str2bool(entry.player.is_live) and not await self.bot.has_tag(ctx.message.author, "donator"):
            await self.bot.edit_message(summon_message, "Playing livestreams is only available to donators.")
            return

        await state.queue.put(entry)
        state.start_loop()

        await self.bot.say(embed=entry.get_embed(action="Enqueued"))
        await self.bot.delete_message(summon_message)

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Skips a song"""
        state = self.get_voice_state(ctx.message)
        #self.get_voice_state(ctx.message).skip()
        #await self.bot.say("\N{OK HAND SIGN}")
        if not state.is_playing():
            await self.bot.say('Not playing any music right now.')
            return

        def role_check(r):
            if r.name in ('Beemo Music', 'Beemo Admin'):
                return True
            return False

        if ctx.message.author.voice_channel is None:
            await self.bot.say("You are not in the voice channel.")
            return

        if checks.role_or_permissions(ctx, role_check, administrator=True):
            await self.bot.say("Skipping..")
            state.skip()
            return

        voter = ctx.message.author
        if voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            votes_needed = int(len(ctx.message.author.voice_channel.voice_members) / 2)
            if total_votes >= votes_needed:
                await self.bot.say("Skipping..")
                state.skip()
            else:
                await self.bot.say('Vote added, currently at **{0}/{1}**'.format(total_votes, votes_needed))
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    @checks.music_or_permissions(administrator=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message)
        if state.is_playing():
            player = state.player
            player.pause()
        await self.bot.say("\N{OK HAND SIGN}")

    @commands.command(pass_context=True, no_pm=True)
    @checks.music_or_permissions(administrator=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message)
        if state.is_playing():
            player = state.player
            player.resume()
        await self.bot.say("\N{OK HAND SIGN}")

    @commands.command(pass_context=True, no_pm=True, name="np")
    async def playing(self, ctx):
        """Shows info about the currently played song."""
        state = self.get_voice_state(ctx.message)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            await self.bot.say(embed=state.current.get_embed("Playing"))

    @commands.command(pass_context=True, no_pm=True)
    async def queue(self, ctx):
        """Displays the music queue."""
        _message = ""
        state = self.get_voice_state(ctx.message)
        if state.current is None:
            _message += "Not playing anything.\n\n"
        else:
            _message += 'Now playing {}\n\n'.format(state.current)
        for num, i in enumerate(state.queue._queue):
            _message += "`{0}.` `{1}` requested by `{2}`\n".format(num+1, i.player.title, i.requester.display_name)
        await self.bot.say(_message)

    @commands.command(pass_context=True, no_pm=True)
    @checks.music_or_permissions(administrator=True)
    async def volume(self, ctx, *, val: int = None):
        """Returns or changes the volume."""
        state = self.get_voice_state(ctx.message)
        if val is None:
            await self.bot.say('The current volume is {:.0%}'.format(state.player.volume))
            return
        if val > 100:
            await self.bot.say("The volume limit is 100%")
            return
        if state.is_playing():
            redis = self.bot.db.get_storage(ctx.message.server)
            player = state.player
            player.volume = val / 100
            await redis.set("volume", player.volume)
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    @checks.music_or_permissions(administrator=True)
    async def disconnect(self, ctx):
        """Disconnects the bot from the voice channel"""
        state = self.get_voice_state(ctx.message)
        await state.disconnect()
        await self.bot.say("Queue concluded.")
        await self.bot.say("If you enjoy Beemo's music feature, please consider donating. Your donation will help us pay for Beemo's expensive servers. By donating, you also get a rank in Beemo's HQ, and autoplay enabled on your guild. https://beemo.club")

    @commands.command(pass_context=True, no_pm=True)
    @checks.music_or_permissions(administrator=True)
    async def musicchannel(self, ctx, *, channel : discord.Channel = None):
        """Selects music channel."""
        redis = self.bot.db.get_storage(ctx.message.server)

        if channel is None:
            await redis.delete("musicchannel")
            await self.bot.say("Cleared the music channel.")
            return

        await redis.set("musicchannel", channel.id)
        await self.bot.say("Set the music channel to **{0.name}** (`{0.id}`)".format(channel))

    @commands.command(no_pm=True, pass_context=True, hidden=True)
    async def summon(self, ctx):
        """Summon the bot into the channel"""
        state = self.get_voice_state(ctx.message)

        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say("You are not in a voice channel.")
            return

        redis = self.bot.db.get_storage(ctx.message.server)
        musicchannel = await redis.get("musicchannel")
        if musicchannel is not None:
            if ctx.message.author.voice_channel.id != musicchannel:
                musicchannelobj = discord.utils.get(ctx.message.server.channels, id=musicchannel)
                if musicchannelobj is not None:
                    await self.bot.say("You must be in the music channel **{0}** to use the bot.".format(musicchannelobj.name))
                    return
                else:
                    await redis.delete("musicchannel")


        state = self.get_voice_state(ctx.message)
        summon_message = await self.bot.say("Attempting to join the voice channel.")
        try:
            if state.voice is None:
                state.voice = await self.bot.join_voice_channel(summoned_channel)
            # else:
            #     await state.voice.move_to(summoned_channel)
        except:
            await self.bot.edit_message(summon_message, "Unable to join the voice channel.")
            return
        await self.bot.edit_message(summon_message, "Joined the voice channel")

        state.start_loop()

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.disconnect())
            except:
                pass