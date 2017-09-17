from discord.ext import commands
from util import checks
from pyfiglet import Figlet
import discord

import aiohttp
import xkcd
import operator
import wolframalpha
import json
import traceback
#import praw

class Misc(object):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.f = Figlet(font='slant')
        #self.r = praw.Reddit(user_agent="Beemo")

    @commands.command(no_pm=True, pass_context=True)
    async def invites(self, ctx, user : discord.Member = None):
        """Displays how many users a user has invited to this guild."""
        if user is None:
            user = ctx.message.author

        try:
            _invites = await self.bot.invites_from(ctx.message.server)
        except:
            await self.bot.say("No permission.")
            return

        invite_count = 0

        for invite in _invites:
            if invite.inviter is not None and invite.inviter.id == user.id:
                invite_count += invite.uses

        await self.bot.say("**{0}** has invited **{1}** users onto this guild.".format(user.name, invite_count))

    @commands.command()
    async def cat(self):
        """Meow!"""
        resp = await self.session.get("http://random.cat/meow")
        image_url = await resp.json()
        resp.close()
        image_url = image_url["file"]

        await self.bot.say(image_url)

    @commands.command()
    async def xkcd(self, *, xkcd_id : int = None):
        """Get a XKCD comic."""
        if xkcd_id is not None:
            future = self.bot.loop.run_in_executor(None, xkcd.getComic, xkcd_id)
        else:
            future = self.bot.loop.run_in_executor(None, xkcd.getRandomComic)

        comic = await future

        _message = "XKCD **{0}**\nLink: {1}".format(comic.getTitle(), comic.getImageLink())
        await self.bot.say(_message)

    @commands.command()
    async def ascii(self, *, text : str):
        """Print some ascii!"""
        future = self.bot.loop.run_in_executor(None, self.f.renderText, text)
        result = await future

        await self.bot.say("```"+result+"```")

    @commands.command()
    async def botlist(self, *, page : int = 1):
        resp = await self.session.get("https://www.carbonitex.net/discord/api/listedbots")

        _resp = await resp.json()
        resp.close()
        resp = _resp

        bot_list = {}

        for bot in resp:
            if int(bot["servercount"]) != 0:
                bot_list[bot["name"]] = int(bot["servercount"])

        sorted_bot_list = sorted(bot_list.items(), key=operator.itemgetter(1), reverse=True)

        bot_list = []

        for num, bot in enumerate(sorted_bot_list):
            bot_name = bot[0]
            server_count = bot[1]

            bot_list.append([num+1, bot_name, server_count])

        bot_list = [bot_list[i:i + 10] for i in range(0, len(bot_list), 10)]

        pages = len(bot_list)

        bot_list = bot_list[page-1]

        _message = "Bot list:\n\nPage {0}/{1}\n\n".format(page, pages)

        for bot_info in bot_list:
            _message += "**{0[0]}**: **{0[1]}** - **{0[2]}** Servers\n".format(bot_info)

        await self.bot.say(_message)

    @commands.command(pass_context=True, aliases=["wa", "wolframalpha", "wolf"])
    async def wolfram(self, ctx, *, statement : str):
        """Wolfram"""
        await self.bot.type()
        api_keys = json.loads(await self.bot.db.redis.get("config:wolfram_key"))
        for api_key in api_keys:
            client = wolframalpha.Client(api_key)

            try:
                res = await self.bot.loop.run_in_executor(None, client.query, statement)
            except:
                traceback.print_exc()
                continue

            res_text = next(res.results).text
            await self.bot.say("`{0}`".format(res_text))
            return

        await self.bot.say("Error making wolfram request, maybe I have hit the maximum API requests?")

    @commands.command(aliases=["p", "bin", "store"])
    async def paste(self, *, content : str):
        resp = await self.session.post(
            "https://zifb.in/api/v1/paste",
            data=json.dumps({
                "paste": content,
                "language": "markdown",
                "expiration": 0
            })
        )

        paste_info = await resp.json()

        resp.close()

        #print(paste_info)

        message = "**URL**: {0}\n\n**Expires**: {1}".format(paste_info["paste"], paste_info["expires"])
        await self.bot.say(message)

    # @commands.command(aliases=["getmeme", "gm"])
    # async def meme(self):
    #     """Returns a random meme"""
    #     sub = await self.bot.loop.run_in_executor(None, self.r.get_subreddit, 'memes')
    #     post = await self.bot.loop.run_in_executor(None, sub.get_random_submission)
    #     await self.bot.say(post.url) 

    # @commands.command(aliases=["atgif"])
    # async def adventuretime(self):
    #     """Returns a adventure time gif"""
    #     sub = await self.bot.loop.run_in_executor(None, self.r.get_subreddit, 'adventuretimegifs')
    #     post = await self.bot.loop.run_in_executor(None, sub.get_random_submission)
    #     await self.bot.say(post.url) 

    # @commands.command(pass_context=True)
    # async def reddit(self, ctx, *, subreddit : str):
    #     """Display a random link from a subreddit."""
    #     sub = await self.bot.loop.run_in_executor(None, self.r.get_subreddit, subreddit)
    #     try:
    #         post = await self.bot.loop.run_in_executor(None, sub.get_random_submission)
    #     except praw.errors.InvalidSubreddit:
    #         await self.bot.say("Subreddit does not exist.")
    #         return

    #     if post.over_18:
    #         nsfw_role = await self.bot.db.get_storage(ctx.message.server).get("nsfw_role")
    #         if nsfw_role is None:
    #             nsfw_role = "Beemo NSFW"

    #         if not self.bot.has_role(ctx.message, nsfw_role):
    #             await self.bot.say("You need the `{0}` role to view this post.".format(nsfw_role))
    #             return

    #     await self.bot.say(post.url) 

    @commands.command(name="strawpoll")
    async def strawpoll(self, *, question, options=None):
        """Makes a poll based on questions and choices or options. must be divided by "; "

Examples:
strawpoll What is this person?; Who is this person?; Where is this person?; When is this person coming?
strawpoll What; Who?; Where?; When?; Why?"""
        options_list = question.split('; ')
        title = options_list[0]
        options_list.remove(title)
        if len(options_list) < 2:
            await self.bot.say("You need to specify 2 or more options")
        else:
            normal = {"title": title, "options": options_list}
            async with self.session.post('http://strawpoll.me/api/v2/polls', 
                                         headers={'content-type': 'application/json'},
                                         data=json.dumps(normal)) as resp:
                result = await resp.json()
                await self.bot.say("**URL**: http://strawpoll.me/{}".format(result["id"]))

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @checks.is_owner()
    async def topbots(self, ctx, *, page : int = 1):
        bots_in_server = [m.id for m in ctx.message.server.members if m.bot]

        bot_list = {}

        #spam carbonitex
        for bot_id in bots_in_server:
            resp = await self.session.get(url="https://www.carbonitex.net/discord/api/bot/info", params={"id": bot_id})

            resp_json = await resp.json()

            if isinstance(resp_json, list):
                continue

            if "name" in resp_json.keys() and "servercount" in resp_json.keys():
                if resp_json["servercount"] is not "0":
                    bot_list[resp_json["name"]] = int(resp_json["servercount"])

            resp.close()

        sorted_bot_list = sorted(bot_list.items(), key=operator.itemgetter(1), reverse=True)

        bot_list = []

        for num, bot in enumerate(sorted_bot_list):
            bot_name = bot[0]
            server_count = bot[1]

            bot_list.append([num+1, bot_name, server_count])

        bot_list = [bot_list[i:i + 10] for i in range(0, len(bot_list), 10)]

        pages = len(bot_list)

        bot_list = bot_list[page-1]

        _message = "Bot list (for this server):\n\nPage {0}/{1}\n\n".format(page, pages)

        for bot_info in bot_list:
            _message += "**{0[0]}**: **{0[1]}** - **{0[2]}** Servers\n".format(bot_info)

        await self.bot.say(_message)

    @commands.command(aliases=["guildlist"])
    async def serverlist(self, *, page : int = 1):
        sorted_server_list = sorted({s.name: len(s.members) for s in self.bot.servers}.items(), key=operator.itemgetter(1), reverse=True)
        server_list = [[num+1, server[0], server[1]] for num, server in enumerate(sorted_server_list)]
        server_list = [server_list[i:i + 10] for i in range(0, len(server_list), 10)]

        pages = len(server_list)
        server_list = server_list[page-1]
        _message = "Servers I am on (Shard {0}/{1}):\n\nPage {2}/{3}\n\n".format(self.bot.shard_id+1, self.bot.shard_count, page, pages)

        for server_info in server_list:
            _message += "**{0[0]}**: **{0[1]}** - **{0[2]}** Members\n".format(server_info)

        await self.bot.say(_message)









def setup(bot):
    bot.add_cog(Misc(bot))