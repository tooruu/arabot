import logging
from base64 import b64encode

from disnake import Embed
from disnake.ext.commands import command
from disnake.utils import escape_markdown

from arabot.core import Category, Cog, Context, StopCommand
from arabot.utils import codeblock

from .translate import GoogleTranslate


class OCRException(Exception):
    def __init__(self, image_url: str, code: int, message: str):
        super().__init__(image_url, code, message)
        self.image_url = image_url
        self.code = code
        self.message = message


class GoogleOCR(Cog, category=Category.LOOKUP, keys={"G_OCR_KEY"}):
    G_OCR_KEY: str

    def __init__(self, trans: GoogleTranslate):
        self.trans = trans

    @command(aliases=["read"], brief="Read text from image", usage="<image or reply>")
    async def ocr(self, ctx: Context):
        await ctx.trigger_typing()
        image_url = await ctx.rsearch(ctx.RSearchTarget.IMAGE_URL)
        text = await self.handle_annotation(ctx, image_url)
        await ctx.send(
            embed=Embed(description=codeblock(text))
            .set_thumbnail(url=image_url)
            .set_footer(
                text="Google Cloud Vision",
                icon_url="http://vision-explorer.reactive.ai/images/Vision-API.png",
            )
        )

    @command(
        aliases=["otr", "ocrt", "octr", "ocrtrans"],
        brief="Read & translate text from image",
        usage="[lang from] [lang to] <image or reply>",
    )
    async def ocrtranslate(self, ctx: Context):
        await ctx.trigger_typing()
        image_url = await ctx.rsearch(ctx.RSearchTarget.IMAGE_URL)
        text = await self.handle_annotation(ctx, image_url)
        langs = await self.trans.gtrans.languages(repr_lang=self.trans.DEFAULT_TARGET[0])
        source, target, _ = self.trans.parse_query(ctx.argument_only, langs)
        translation = await self.trans.handle_translation(ctx, source, target, text, langs)
        (source, text), (target, trans_text) = translation
        embed = Embed().set_thumbnail(url=image_url)
        if source[0] != target[0]:
            embed.add_field(self.trans.format_lang(source), escape_markdown(text)[:1024])
        embed.add_field(
            self.trans.format_lang(target), escape_markdown(trans_text)[:1024], inline=False
        )
        await ctx.send(embed=embed)

    async def handle_annotation(self, ctx: Context, image_url: str | None) -> str:
        if not image_url and not (image_url := await ctx.rsearch(ctx.RSearchTarget.IMAGE_URL)):
            await ctx.send_("no_image_or_link_provided")
            raise StopCommand

        try:
            text = await self.annotate(image_url)
        except OCRException:
            async with ctx.ara.session.get(image_url) as resp:
                if not resp.ok:
                    logging.warning("OCR: Couldn't download image %s", image_url)
                    await ctx.reply_("couldnt_read_image")
                    raise StopCommand from None
                image_data = await resp.read()
            try:
                text = await self.annotate(image_data)
            except OCRException:
                logging.warning("OCR: Image failed %s", image_url)
                await ctx.reply_("couldnt_read_image")
                raise StopCommand from None

        if not text:
            await ctx.reply_("no_text")
            raise StopCommand

        return text

    async def annotate(self, image: str | bytes) -> str | None:
        data = await self.trans.gtrans.session.fetch_json(  # lol
            f"https://vision.googleapis.com/v1/images:annotate?key={self.G_OCR_KEY}",
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
