import aiohttp

async def paste(content):
	async with aiohttp.ClientSession().post("https://pybin.pw/documents", data=content) as resp:
		json_resp = await resp.json()
		content = "https://pybin.pw/"+json_resp["key"]
		resp.close()
	return content