from aiohttp import ClientSession
from disnake.ext.commands import command

from arabot.core import Category, Cog, Context


class Youtube(Cog, category=Category.LOOKUP, keys={"G_YT_KEY"}):
    G_YT_KEY: str
    YT_BASE_URL = "https://www.googleapis.com/youtube/v3/search"

    def __init__(self, session: ClientSession):
        self.session = session

    @command(aliases=["yt"], brief="Show top search result from YouTube")
    async def youtube(self, ctx: Context, *, query: str):
        data = await self.session.fetch_json(
            self.YT_BASE_URL,
            params={
                "key": self.G_YT_KEY,
                "q": query,
                "maxResults": 1,
                "type": "video",
                "regionCode": "US",
            },
        )
        await ctx.reply(
            "https://youtu.be/" + data["items"][0]["id"]["videoId"]
            if data.get("items")
            else ctx._("no_videos_found")
        )
