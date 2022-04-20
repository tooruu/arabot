import re
from functools import partial

from arabot.core import Category, Cog, Context
from arabot.utils import dsafe
from disnake import Embed
from disnake.ext.commands import command
from disnake.utils import find

from .client import TranslationClient
from .types import LangCodeAndOrName


class Translate(Cog, category=Category.LOOKUP):
    DEFAULT_TARGET = ["en", "English"]

    def __init__(self, trans_client: TranslationClient):
        self.gtrans = trans_client

    @command(aliases=["tr", "trans"], brief="Translates text")
    async def translate(self, ctx: Context, *query):
        if not query:
            if not (query := await ctx.message.rsearch(ctx, "content")):
                await ctx.reply("I need text to translate!")
                return
            query = query.split(" ")  # TODO: Add languages support

        all_langs = await self.gtrans.languages(target=self.DEFAULT_TARGET[0])
        source, target, text = self.parse_query(query, all_langs)

        translated, detect_lang = await self.gtrans.translate(text, target[0], source and source[0])
        if detect_lang:  # Exists only if source is None (auto-detect)
            source = self.find_lang(detect_lang, all_langs)

        if source == target:
            await ctx.reply("I can't translate from the same language to itself!")
            return

        embed = (
            Embed()
            .add_field(name=self.format_lang(source), value=dsafe(text)[:1024])
            .add_field(name=self.format_lang(target), value=dsafe(translated)[:1024], inline=False)
        )
        await ctx.send(embed=embed)

    def parse_query(
        self, query: str, langs: list[LangCodeAndOrName]
    ) -> tuple[LangCodeAndOrName | None, LangCodeAndOrName, str]:
        find_lang = partial(self.find_lang, langs=langs)
        match query:
            case [source, target, *text] if text:
                text = " ".join(text)

                if temp := find_lang(source):
                    source = temp
                    if temp := find_lang(target):
                        target = temp
                    else:
                        text = f"{target} {text}"
                        target = source
                        source = None
                else:
                    text = f"{source} {target} {text}"
                    target = self.DEFAULT_TARGET
                    source = None

            case [target, text]:
                source = None

                if temp := find_lang(target):
                    target = temp
                else:
                    text = f"{target} {text}"
                    target = self.DEFAULT_TARGET

            case [text]:
                target = self.DEFAULT_TARGET
                source = None

            case _:
                raise ValueError("Empty query")

        return source, target, text

    @staticmethod
    def find_lang(string: str, langs: list[LangCodeAndOrName]) -> LangCodeAndOrName | None:
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
