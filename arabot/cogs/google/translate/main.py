import re
from functools import partial

from arabot.core import Category, Cog, Context
from arabot.utils import dsafe
from disnake import Embed
from disnake.ext.commands import command
from disnake.utils import find

from .client import LangCodeAndOrName, TranslationClient


class Translate(Cog, category=Category.LOOKUP):
    DEFAULT_TARGET: list[str] = ["en", "English"]

    def __init__(self, trans_client: TranslationClient):
        self.gtrans = trans_client

    @command(aliases=["tr", "trans"], brief="Translates text")
    async def translate(self, ctx: Context, *query):
        langs = await self.gtrans.languages(target=self.DEFAULT_TARGET[0])
        source, target, text = self.parse_query(query, langs)

        if not text and not (text := await ctx.rsearch("content")):
            await ctx.send("I need text to translate")
            return

        if not source:
            detected = await self.detect_language(text)
            source = self.find_lang(detected, langs)
            if not source:
                await ctx.send("Couldn't detect language")
                return

        target = target or self.DEFAULT_TARGET
        if source == target:
            await ctx.reply("Cannot translate to the same language")
            return

        translation = await self.gtrans.translate(text, target[0], source[0])[0]
        embed = (
            Embed()
            .add_field(name=self.format_lang(source), value=dsafe(text)[:1024])
            .add_field(name=self.format_lang(target), value=dsafe(translation)[:1024], inline=False)
        )
        await ctx.send(embed=embed)

    def parse_query(
        self, query: str, langs: list[LangCodeAndOrName]
    ) -> tuple[LangCodeAndOrName | None, LangCodeAndOrName | None, str | None]:
        find_lang = partial(self.find_lang, langs=langs)
        match query:
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

            case [str1, str2, *text]:
                text = " ".join(text)
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
        if not string:
            return None
        return find(lambda lang: re.fullmatch("|".join(lang), string, re.IGNORECASE), langs)

    @staticmethod
    def format_lang(lang: LangCodeAndOrName) -> str:
        if not lang:
            raise ValueError("Empty language")

        field_name = lang[0].upper()
        if lang[1:]:
            field_name += " - " + lang[1].title()
        return field_name

    def cog_unload(self) -> None:
        self.gtrans._invalidate_language_cache.stop()
