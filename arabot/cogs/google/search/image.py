import logging
from io import BytesIO
from mimetypes import guess_extension
from pathlib import Path

import disnake
from aiohttp import ClientResponse, ClientSession
from arabot.core import Category, Cog, Context
from disnake.ext.commands import command


class ImageSearch(Cog, category=Category.LOOKUP, keys={"g_isearch_key", "g_cse"}):
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    SVG_MIME = "image/svg+xml"

    def __init__(self, session: ClientSession):
        self.session = session

    @command(aliases=["i", "img"], brief="Top search result from Google Images")
    async def image(self, ctx: Context, *, query):
        async with ctx.typing():
            images = await self.fetch_images(query)
            async for image_file in self.filtered(images):
                await ctx.reply(file=image_file)
                break
            else:
                await ctx.reply("No images found")

    async def fetch_images(self, query) -> list:
        data = await self.session.fetch_json(
            self.BASE_URL,
            params={
                "key": self.g_isearch_key,
                "cx": self.g_cse,
                "q": f"{query} -filetype:svg",
                "searchType": "image",
            },
        )

        return data.get("items", [])

    async def filtered(self, images: list[dict]) -> disnake.File:
        for item in images:
            if self.SVG_MIME in (item.get("mime"), item.get("fileFormat")):
                continue

            image_url = item["link"]
            try:
                async with self.session.get(image_url) as resp:
                    if (
                        not resp.ok
                        or resp.content_type == self.SVG_MIME
                        or not resp.content_type.startswith("image/")
                    ):
                        continue
                    image = await resp.read()
            except Exception as e:
                logging.error("%s\nFailed image: %s", e, image_url)
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
