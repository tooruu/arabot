from urllib.parse import quote_plus

from aiohttp import ClientSession
from disnake import Embed
from disnake.ext.commands import command

from arabot.core import Category, Cog, Context


class GoogleSearch(Cog, category=Category.LOOKUP, keys={"G_SEARCH_KEY", "G_CSE"}):
    G_SEARCH_KEY: str
    G_CSE: str
    GSEARCH_BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, session: ClientSession):
        self.session = session

    @command(aliases=["g"], brief="Show top Google Search result")
    async def google(self, ctx: Context, *, query: str):
        json = await self.session.fetch_json(
            self.GSEARCH_BASE_URL,
            params={
                "key": self.G_SEARCH_KEY,
                "cx": self.G_CSE,
                "q": query,
                "num": 1,
            },
        )
        await ctx.reply(
            json["items"][0]["link"] if json.get("items") else ctx._("no_results", False)
        )

    @command(aliases=["g3"], brief="Show top 3 Google Search results")
    async def google3(self, ctx: Context, *, query: str):
        data = await self.session.fetch_json(
            self.GSEARCH_BASE_URL,
            params={
                "key": self.G_SEARCH_KEY,
                "cx": self.G_CSE,
                "q": query,
                "num": 3,
            },
        )

        if not data.get("items"):
            await ctx.reply_("no_results", False)
            return

        embed = Embed(
            title="Google Search",
            url=f"https://google.com/search?q={quote_plus(query)}",
        )

        for hit in data["items"]:
            url: str = hit["link"]
            bc = self.generate_breadcrumbs(url)
            embed.add_field(hit["title"], f"[{bc}]({url})\n{hit['snippet']}", inline=False)
        await ctx.reply(embed=embed)

    @staticmethod
    def generate_breadcrumbs(url: str, num_parts: int = 4) -> str:
        breadcrumbs = url.partition("?")[0].removesuffix("/").split("/")[2 : 2 + num_parts]
        breadcrumbs[0] = max(breadcrumbs[0].removeprefix("www.").split("."), key=len)
        return " > ".join(s.replace("_", " ").replace("-", " ").capitalize() for s in breadcrumbs)
