from .player import create_ffmpeg_player

import asyncio
import youtube_dl
import functools

async def extract_info(loop, url, ytdl_options):

    opts = {
        'format': 'webm[abr>0]/bestaudio/best'
    }

    if ytdl_options is not None and isinstance(ytdl_options, dict):
        opts.update(ytdl_options)

    ydl = youtube_dl.YoutubeDL(opts)
    func = functools.partial(ydl.extract_info, url, download=False)
    info = await loop.run_in_executor(None, func)
    if "entries" in info:
        info = info['entries'][0]

    cache_info = {
        "url": url,
        "download_url": info.get("url"),
        "title": info.get("title"),
        "duration": info.get("duration"),
        "is_live": bool(info.get("is_live"))
        }

    thumbnails = info.get("thumbnails")

    if thumbnails is not None and len(thumbnails) > 0:
        thumbnail = thumbnails[0]
        thumbnail_url = thumbnail.get("url")
        if thumbnail_url:
            cache_info["thumbnail"] = thumbnail_url

    cache_info = {k: str(v) for k, v in cache_info.items()}

    return cache_info

async def generate_ytdl_player(state, url, **kwargs):
    if url not in await state.bot.db.cache_redis.keys("*"):
        cache_info = await extract_info(state.bot.loop, url, kwargs.get("ytdl_options"))

        await state.bot.db.cache_redis.hmset_dict(url, cache_info)
        await state.bot.db.cache_redis.hmset_dict(cache_info["title"], cache_info)

        await state.bot.db.cache_redis.expire(url, 7200)
        await state.bot.db.cache_redis.expire(cache_info["title"], 7200)

    kwargs.pop("ytdl_options")

    download_url = await state.bot.db.cache_redis.hget(url, "download_url")
    player = create_ffmpeg_player(state.voice, download_url, **kwargs)

    player_info = await state.bot.db.cache_redis.hgetall(url)

    for k,v in player_info.items():
        setattr(player, k, v)

    return player