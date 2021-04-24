from io import BytesIO
from aiohttp import ClientResponseError
from urllib.parse import quote_plus as safe, urlparse
from discord import Embed, File
from discord.ext.commands import command, Cog, ConversionError
from ...utils.format_escape import bold
from ...utils.general import QueryFilter, BlacklistMatch
from ...helpers.auth import req_auth


class Google(Cog, name="Commands"):
    def __init__(self, client, keys):
        self.bot = client
        (self.g_search_key, self.g_isearch_key, self.g_cse, self.g_yt_key) = keys

    @command(aliases=["i", "img"], brief="<query> | Top search result from Google Images")
    async def image(self, ctx, *, query: QueryFilter):
        try:
            json = await self.bot.fetch_json(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": self.g_isearch_key,
                    "cx": self.g_cse,
                    "q": safe(query),
                    "num": 10,
                    "searchType": "image",
                },
            )
        except ClientResponseError as e:
            if e.status == 429:
                await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>")
                return
            raise
        for i in json.get("items", ()):
            try:
                async with self.bot.ses.get(i["link"]) as image:
                    if image.ok and image.content_type.startswith("image/"):
                        filename = urlparse(i["link"])[2].split("/")[-1]
                        image = BytesIO(await image.read())
                        await ctx.send(file=File(image, filename + ".jpg"))
                        return
            except Exception as e:
                print(e, "\nFailed image link: ", i["link"])
        await ctx.send("No images found")

    @image.error
    async def use_tags(self, ctx, error):
        if isinstance(error, ConversionError) and isinstance(error.original, BlacklistMatch):
            await ctx.send(error.original.desc)
            return
        raise error

    @command(aliases=["g"], brief="<query> | Top Google Search result")
    async def google(self, ctx, *, query):
        try:
            json = await self.bot.fetch_json(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": self.g_search_key, "cx": self.g_cse, "q": query, "num": 1},
            )
        except ClientResponseError as e:
            if e.status == 429:
                await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>")
            raise
        await ctx.send(json["items"][0]["link"] if json["items"] else "No results found")

    @command(aliases=["g3"], brief="<query> | Top 3 Google Search results")
    async def google3(self, ctx, *, query):
        try:
            json = await self.bot.fetch_json(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": self.g_search_key,
                    "cx": self.g_cse,
                    "q": safe(query),
                    "num": 3,
                },
            )
        except ClientResponseError as e:
            if e.status == 429:
                await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>")
                return
            raise
        if json["items"]:
            embed = Embed(
                title="Google search results",
                description="Showing top 3 search results",
                url="https://google.com/search?q=" + safe(query),
            )
            for hit in json["items"]:
                embed.add_field(
                    name=hit["link"],
                    value=f"{bold(hit['title'])}\n{hit['snippet']}",
                    inline=False,
                )
            await ctx.send(embed=embed)
            return
        await ctx.send("No results found")

    @command(aliases=["yt"], brief="<query> | Top search result from YouTube")
    async def youtube(self, ctx, *, query):
        try:
            json = await self.bot.fetch_json(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "key": self.g_yt_key,
                    "q": query,
                    "maxResults": 1,
                    "type": "video",
                    "regionCode": "US",
                },
            )
        except ClientResponseError as e:
            if e.status == 429:
                await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>")
            raise
        await ctx.send("https://youtu.be/" + json["items"][0]["id"]["videoId"] if json["items"] else "No videos found")

    @command(aliases=["yt3"], brief="<query> | Top 3 search results from YouTube")
    async def youtube3(self, ctx, *, query):
        try:
            json = await self.bot.fetch_json(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "key": self.g_yt_key,
                    "q": query,
                    "maxResults": 3,
                    "type": "video",
                    "regionCode": "US",
                },
            )
        except ClientResponseError as e:
            if e.status == 429:
                await ctx.send("Sorry, I've hit today's 100 queries/day limit <:MeiStare:697945045311160451>")
            raise
        await ctx.send(
            "\n".join(["https://youtu.be/" + hit["id"]["videoId"] for hit in json["items"]])
            if json["items"]
            else "No videos found"
        )


@req_auth("g_search_key", "g_isearch_key", "g_cse", "g_yt_key")
def setup(client, keys):
    client.add_cog(Google(client, keys))
