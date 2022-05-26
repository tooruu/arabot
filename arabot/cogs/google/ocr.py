import logging
from base64 import b64encode

from aiohttp import ClientSession
from arabot.core import Category, Cog, Context
from arabot.core.utils import codeblock
from disnake import Embed
from disnake.ext.commands import command


class OCRException(Exception):
    def __init__(self, image_url: str, code: int, message: str):
        super().__init__(image_url, code, message)
        self.image_url = image_url
        self.code = code
        self.message = message


class OpticalCharacterRecognition(Cog, category=Category.LOOKUP, keys={"g_ocr_key"}):
    def __init__(self, session: ClientSession):
        self.session = session

    @command(aliases=["read"], brief="Read text from image")
    async def ocr(self, ctx: Context):
        await ctx.trigger_typing()
        image_url = await ctx.rsearch("image_url")
        if not image_url:
            await ctx.send("No image or link provided")
            return

        try:
            text = await self.annotate(image_url)
        except OCRException:
            async with self.session.get(image_url) as resp:
                if not resp.ok:
                    logging.warning("OCR: Couldn't download image %s", image_url)
                    await ctx.reply("Couldn't read image")
                    return
                image_data = await resp.read()
            try:
                text = await self.annotate(image_data)
            except OCRException:
                logging.warning("OCR: Image failed %s", image_url)
                await ctx.reply("Couldn't read image")
                return

        if not text:
            await ctx.send("No text found")
            return

        await ctx.send(
            embed=Embed(description=codeblock(text))
            .set_thumbnail(url=image_url)
            .set_footer(
                text="Powered by Google Cloud Vision",
                icon_url="http://vision-explorer.reactive.ai/images/Vision-API.png",
            )
            .with_author(ctx.author)
        )

    async def annotate(self, image: str | bytes) -> str | None:
        data = await self.session.fetch_json(
            f"https://vision.googleapis.com/v1/images:annotate?key={self.g_ocr_key}",
            method="post",
            json={
                "requests": [
                    {
                        "image": {"source": {"imageUri": image}}
                        if isinstance(image, str)
                        else {"content": b64encode(image).decode()},
                        "features": [{"type": "TEXT_DETECTION"}],
                    }
                ]
            },
        )
        response: dict[str, dict] = data["responses"][0]
        if error := response.get("error"):
            raise OCRException(image, error["code"], error["message"])
        if "fullTextAnnotation" not in response:
            return None
        return response["fullTextAnnotation"]["text"]
