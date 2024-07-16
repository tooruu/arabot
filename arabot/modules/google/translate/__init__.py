import re
from functools import partial
from typing import ClassVar

from disnake import Embed
from disnake.ext.commands import command
from disnake.utils import escape_markdown, find

from arabot.core import Category, Cog, Context, StopCommand

from .client import LangCodeAndOrName, TranslationClient


class GoogleTranslate(Cog, category=Category.LOOKUP):
    DEFAULT_TARGET: ClassVar[LangCodeAndOrName] = ["en", "English"]

    def __init__(self, trans_client: TranslationClient):
        self.gtrans = trans_client

    @command(
        aliases=["tr", "trans"],
        brief="Translates text",
        usage="[lang from] [lang to] <text or reply>",
    )
    async def translate(self, ctx: Context):
        langs = await self.gtrans.languages(repr_lang=self.DEFAULT_TARGET[0])
        user_args = self.parse_query(ctx.argument_only, langs)
        translation = await self.handle_translation(ctx, *user_args, langs)
        (source, text), (target, translated_text) = translation
        if source[0] == target[0]:
            await ctx.reply_("same_language")
            return
        await ctx.send(
            embed=Embed()
            .add_field(self.format_lang(source), escape_markdown(text)[:1024])
            .add_field(
                self.format_lang(target), escape_markdown(translated_text)[:1024], inline=False
            )
            .set_footer(
                text="Google Cloud Translation",
                icon_url="https://gitlab.com/uploads/-/system"
                "/project/avatar/12400259/Cloud_Translation_API.png",
            )
        )

    async def handle_translation(
        self,
        ctx: Context,
        source: LangCodeAndOrName | None,
        target: LangCodeAndOrName | None,
        text: str | None,
        langs: list[LangCodeAndOrName],
    ) -> tuple[tuple[LangCodeAndOrName, str], tuple[LangCodeAndOrName, str]]:
        if not text and not (text := await ctx.rsearch(ctx.RSearchTarget.CONTENT)):
            await ctx.reply_("provide_text")
            raise StopCommand
        if not source:
            detected = await self.gtrans.detect(text)
            if not (source := self.find_lang(detected, langs)):
                await ctx.reply_("unknown_language")
                raise StopCommand
        target = target or self.DEFAULT_TARGET
        if source[0] == target[0]:
            translated_text = text
        else:
            translated_text, _ = await self.gtrans.translate(text, target[0], source[0])
        return (source, text), (target, translated_text)

    def parse_query(
        self, query: str, langs: list[LangCodeAndOrName]
    ) -> tuple[LangCodeAndOrName | None, LangCodeAndOrName | None, str | None]:
        find_lang = partial(self.find_lang, langs=langs)
        match query.split(maxsplit=2):
            case []:
                source = target = text = None

            case [str1]:
                source = None
                text = None if (target := find_lang(str1)) else str1

            case [str1, str2]:
                if source := find_lang(str1):
                    if target := find_lang(str2):
                        text = None
                    else:
                        source, target = None, source
                        text = str2
                else:
                    target = None
                    text = f"{str1} {str2}"

            case [str1, str2, text]:
                if source := find_lang(str1):
                    if not (target := find_lang(str2)):
                        source, target = None, source
                        text = f"{str2} {text}"
                else:
                    target = None
                    text = f"{str1} {str2} {text}"

        return source, target, text

    @staticmethod
    def find_lang(string: str, langs: list[LangCodeAndOrName]) -> LangCodeAndOrName | None:
        if string:
            return find(lambda lang: re.fullmatch("|".join(lang), string, re.IGNORECASE), langs)
        return None

    @staticmethod
    def format_lang(lang: LangCodeAndOrName) -> str:
        if not lang:
            raise ValueError("Empty language")

        field_name = lang[0].upper()
        if lang[1:]:
            field_name += f" - {lang[1].title()}"
        return field_name

    def cog_unload(self) -> None:
        self.gtrans._invalidate_language_cache.stop()
