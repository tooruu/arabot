from re import match
from urllib.parse import quote
from aiohttp import ContentTypeError
from discord import Embed
from discord.ext.commands import command, Cog
from jikanpy import AioJikan
from ...utils.format_escape import dsafe


class Sauce(Cog, name="Commands"):
    def __init__(self, client):
        self.bot = client

    @command(aliases=["source"], brief="<link|attachment> | Find anime source for an image")
    async def sauce(self, ctx, image_url=None):
        if ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
        elif not match(r"https?://(-\.)?([^\s/?\.#]+\.?)+(/[^\s]*)?$", image_url):
            await ctx.reply("Bad image URL")
            return
        async with ctx.typing(), self.bot.ses.get("https://trace.moe/api/search?url=" + quote(image_url)) as tmoe_resp:
            try:
                mal_resp = await AioJikan(session=self.bot.ses).anime(
                    (tmoe_resp := (await tmoe_resp.json())["docs"][0])["mal_id"]
                )
            except ContentTypeError:
                await ctx.send("<https://trace.moe> rejected the image")
                return

            episode = None
            if tmoe_resp["episode"]:
                episode = f"Episode {tmoe_resp['episode']} ({int(tmoe_resp['at']/60)}:{int(tmoe_resp['at']%60):02d})"
            desc = f"Similarity: {tmoe_resp['similarity']:.1%} | Score: {mal_resp['score']} | {mal_resp['status']}"
            synopsis = dsafe(mal_resp["synopsis"].partition(" [")[0])
            if len(synopsis) > (maxlength := 600):
                synopsis = ".".join(synopsis[:maxlength].split(".")[0:-1]) + "..."
            embed = (
                Embed(color=32767, description=desc)
                .set_author(name=mal_resp["title"], url=mal_resp["url"])
                .set_thumbnail(url=mal_resp["image_url"])
                .add_field(name="Synopsis", value=synopsis)
                .set_footer(
                    text=f"Requested by {ctx.author.display_name} | Powered by trace.moe",
                    icon_url=ctx.author.avatar_url_as(static_format="png"),
                )
            )
            await ctx.send(episode, embed=embed)


def setup(client):
    client.add_cog(Sauce(client))
