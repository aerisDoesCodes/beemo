from util.paste import paste

import aiohttp
import json



class WebHook(object):
    def __init__(self, url, shard_id):
        self.url = url
        self.shard_id = shard_id+1

    async def log(self, message):
        if len(message) > 1000:
            message = await paste(message)

        data = json.dumps({"content": "**Shard {0}** ".format(self.shard_id)+message})
        headers = {
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            resp = await session.post(self.url, headers=headers, data=data)
            session.close()
            resp.close()
