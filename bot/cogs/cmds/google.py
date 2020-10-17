from discord.ext.commands import command, Cog
from discord import Embed
from .._utils import getenv, bold
from urllib.parse import quote_plus as safe
from aiohttp.client_exceptions import ClientConnectorError

class Google(Cog, name="Commands"):
	def __init__(self, client):
		self.bot = client
		(self.g_search_key, self.g_isearch_key, self.g_cse, self.g_yt_key) = getenv("g_search_key", "g_isearch_key", "g_cse", "g_yt_key")

	@command(aliases=["i", "img"], brief="<query> | Top search result from Google Images")
	async def image(self, ctx, *, query):
		NUM = 3
		async with self.bot.ses.get(
			"https://www.googleapis.com/customsearch/v1",
			params={
				"key": self.g_isearch_key,
				"cx": self.g_cse,
				"q": safe(query),
				"num": NUM,
				"searchType": "image"
			}
		) as resp:
			if resp.status == 429:
				await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>")
			elif "items" in (resp := await resp.json()):
				blacklist =("lookaside.fbsbx.com",)
				for i in resp["items"]:
					if i["link"].split('/')[2] not in blacklist:
						try:
							async with self.bot.ses.get(i["link"]) as s:
								if s.status == 200:
									await ctx.send(i["link"])
									return
						except ClientConnectorError:
							pass
				await ctx.send(f"First {NUM} links are dead, and I don't want to eat up the quota by requesting more images, so try something else. :slight_smile:")
			else:
				await ctx.send("No images found")

	@command(aliases=["g"], brief="<query> | Top Google Search result")
	async def google(self, ctx, *, query):
		async with self.bot.ses.get(
			"https://www.googleapis.com/customsearch/v1",
			params={
				"key": self.g_search_key,
				"cx": self.g_cse,
				"q":  query,
				"num": 1
			}
			) as resp:
				await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>" if resp.status == 429 else resp["items"][0]["link"] if (resp:=await resp.json())["items"] else "No results found")

	@command(aliases=["g3"], brief="<query> | Top 3 Google Search results")
	async def google3(self, ctx, *, query):
		async with self.bot.ses.get(
			"https://www.googleapis.com/customsearch/v1",
			params={
				"key": self.g_search_key,
				"cx": self.g_cse,
				"q": safe(query),
				"num": 3
			}
			) as resp:
				if resp.status == 429:
					await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>")
				elif (resp:=await resp.json())["items"]:
					embed = Embed(
						title="Google search results",
						description="Showing top 3 search results",
						url="https://google.com/search?q=" + safe(query)
					)
					for hit in resp["items"]:
						embed.add_field(
							name=hit["link"], value=f"{bold(hit['title'])}\n{hit['snippet']}", inline=False
						)
					await ctx.send(embed=embed)
				else:
					await ctx.send("No results found")

	@command(aliases=["yt"], brief="<query> | Top search result from YouTube")
	async def youtube(self, ctx, *, query):
		async with self.bot.ses.get(
			"https://www.googleapis.com/youtube/v3/search",
			params={
				"key": self.g_yt_key,
				"q": query,
				"maxResults": 1,
				"type": "video",
				"regionCode": "US"
			}
		) as resp:
			await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>" if resp.status == 429 else "https://youtu.be/" + resp["items"][0]["id"]["videoId"] if (resp:=await resp.json())["items"] else "No videos found")

	@command(aliases=["yt3"], brief="<query> | Top 3 search results from YouTube")
	async def youtube3(self, ctx, *, query):
		async with self.bot.ses.get(
			"https://www.googleapis.com/youtube/v3/search",
			params={
				"key": self.g_yt_key,
				"q": query,
				"maxResults": 3,
				"type": "video",
				"regionCode": "US"
			}
		) as resp:
			await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>" if resp.status == 429 else '\n'.join(["https://youtu.be/" + hit["id"]["videoId"] for hit in resp["items"]]) if (resp:=await resp.json())["items"] else "No videos found")

def setup(client):
	client.add_cog(Google(client))
