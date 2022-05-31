import logging
from base64 import b64encode

from arabot.core import Category, Cog, Context
from arabot.core.utils import codeblock, dsafe
from disnake import Embed
from disnake.ext.commands import command

from .translate import GoogleTranslate


class OCRException(Exception):
    def __init__(self, image_url: str, code: int, message: str):
        super().__init__(image_url, code, message)
        self.image_url = image_url
        self.code = code
        self.message = message


class GoogleOCR(Cog, category=Category.LOOKUP, keys={"g_ocr_key"}):
    def __init__(self, trans: GoogleTranslate):
        self.trans = trans

    @command(aliases=["read"], brief="Read text from image")
    async def ocr(self, ctx: Context):
        await ctx.trigger_typing()
        image_url = await ctx.rsearch("image_url")
        if text := await self.handle_annotation(ctx, image_url):
            await ctx.send(
                embed=Embed(description=codeblock(text))
                .set_thumbnail(url=image_url)
                .set_footer(
                    text="Google Cloud Vision",
                    icon_url="http://vision-explorer.reactive.ai/images/Vision-API.png",
                )
            )

    @command(aliases=["otr", "ocrt", "octr", "ocrtrans"], brief="Read & translate text from image")
    async def ocrtranslate(self, ctx: Context):
        await ctx.trigger_typing()
        image_url = await ctx.rsearch("image_url")
        if not (text := await self.handle_annotation(ctx, image_url)):
            return

        langs = await self.trans.gtrans.languages(repr_lang=self.trans.DEFAULT_TARGET[0])
        source, target, _ = self.trans.parse_query(ctx.argument_only, langs)
        if translation := await self.trans.handle_translation(ctx, source, target, text, langs):
            (source, text), (target, trans_text) = translation
            await ctx.send(
                embed=Embed()
                .set_thumbnail(url=image_url)
                .add_field(self.trans.format_lang(source), dsafe(text)[:1024])
                .add_field(self.trans.format_lang(target), dsafe(trans_text)[:1024], inline=False)
            )

    async def handle_annotation(self, ctx: Context, image_url: str | None) -> str | None:
        if not image_url and not (image_url := await ctx.rsearch("image_url")):
            await ctx.send("No image or link provided")
            return None

        try:
            text = await self.annotate(image_url)
        except OCRException:
            async with ctx.ara.session.get(image_url) as resp:
                if not resp.ok:
                    logging.warning("OCR: Couldn't download image %s", image_url)
                    await ctx.reply("Couldn't read image")
                    return None
                image_data = await resp.read()
            try:
                text = await self.annotate(image_data)
            except OCRException:
                logging.warning("OCR: Image failed %s", image_url)
                await ctx.reply("Couldn't read image")
                return None

        if not text:
            await ctx.reply("No text found")
            return None

        return text

    async def annotate(self, image: str | bytes) -> str | None:
        data = await self.trans.gtrans.session.fetch_json(  # lol
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
        return response["fullTextAnnotation"]["text"] if "fullTextAnnotation" in response else None
