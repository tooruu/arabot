import logging
from asyncio import TimeoutError
from collections.abc import AsyncIterator
from io import BytesIO
from mimetypes import guess_extension
from pathlib import Path

import disnake
from aiohttp import ClientError, ClientResponse, ClientSession
from disnake.ext.commands import command

from arabot.core import Category, Cog, Context

SVG_MIME = "image/svg+xml"


class GoogleImages(Cog, category=Category.LOOKUP, keys={"G_ISEARCH_KEY", "G_CSE"}):
    G_ISEARCH_KEY: str
    G_CSE: str
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, session: ClientSession):
        self.session = session

    @command(aliases=["i", "img"], brief="Top search result from Google Images")
    async def image(self, ctx: Context, *, query: str):
        async with ctx.typing():
            images = await self.fetch_images(query, ctx.channel.is_nsfw())
            async for image_file in self.filtered(images):
                await ctx.reply(file=image_file)
                break
            else:
                await ctx.reply_("no_images_found")

    async def fetch_images(self, query: str, nsfw: bool = True) -> list[dict]:
        data = await self.session.fetch_json(
            self.BASE_URL,
            params={
                "key": self.G_ISEARCH_KEY,
                "cx": self.G_CSE,
                "q": f"{query} -filetype:svg",
                "searchType": "image",
                "safe": "off" if nsfw else "active",
            },
        )
        return data.get("items", [])

    async def filtered(self, images: list[dict]) -> AsyncIterator[disnake.File]:
        for item in images:
            if SVG_MIME in (item.get("mime"), item.get("fileFormat")):
                continue

            image_url = item["link"]
            try:
                async with self.session.get(image_url, timeout=1.5) as resp:
                    if (
                        not resp.ok
                        or resp.content_type == SVG_MIME
                        or not resp.content_type.startswith("image/")
                    ):
                        continue
                    image = await resp.read()
            except TimeoutError:
                continue
            except ClientError:
                logging.exception("Failed image: %s", image_url)
            else:
                image = BytesIO(image)
                filename = self.extract_filename(resp)
                yield disnake.File(image, filename)

    @staticmethod
    def extract_filename(response: ClientResponse) -> str:
        fn = Path(
            getattr(response.content_disposition, "filename", response.url.path) or "image"
        ).stem
        ext = guess_extension(response.headers.get("Content-Type", ""), strict=False) or ".png"

        return fn + ext
