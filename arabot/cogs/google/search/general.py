from urllib.parse import quote_plus

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import bold
from disnake import Embed
from disnake.ext.commands import command


class GSearch(Cog, category=Category.LOOKUP, keys={"g_search_key", "g_cse", "g_yt_key"}):
    GSEARCH_BASE_URL = "https://www.googleapis.com/customsearch/v1"
    YT_BASE_URL = "https://www.googleapis.com/youtube/v3/search"

    def __init__(self, ara: Ara):
        self.ara = ara

    @command(aliases=["g"], brief="Top Google Search result")
    async def google(self, ctx: Context, *, query):
        json = await self.ara.session.fetch_json(
            self.GSEARCH_BASE_URL,
            params={
                "key": self.g_search_key,
                "cx": self.g_cse,
                "q": query,
                "num": 1,
            },
        )
        await ctx.reply(json["items"][0]["link"] if json.get("items") else "No results found")

    @command(aliases=["g3"], brief="Top 3 Google Search results")
    async def google3(self, ctx: Context, *, query):
        data = await self.ara.session.fetch_json(
            self.GSEARCH_BASE_URL,
            params={
                "key": self.g_search_key,
                "cx": self.g_cse,
                "q": query,
                "num": 3,
            },
        )

        if not data.get("items"):
            await ctx.reply("No results found")
            return

        embed = Embed(
            title="Google search results",
            description="Showing top 3 search results",
            url="https://google.com/search?q=" + quote_plus(query),
        )
        for hit in data["items"]:
            embed.add_field(
                name=hit["link"],
                value=f"{bold(hit['title'])}\n{hit['snippet']}",
                inline=False,
            )
        await ctx.reply(embed=embed)

    @command(aliases=["yt"], brief="Top search result from YouTube")
    async def youtube(self, ctx: Context, *, query):
        data = await self.ara.session.fetch_json(
            self.YT_BASE_URL,
            params={
                "key": self.g_yt_key,
                "q": query,
                "maxResults": 1,
                "type": "video",
                "regionCode": "US",
            },
        )
        await ctx.reply(
            "https://youtu.be/" + data["items"][0]["id"]["videoId"]
            if data.get("items")
            else "No videos found"
        )
