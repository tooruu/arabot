import datetime
import logging
import re
from base64 import b64decode
from functools import partial
from io import BytesIO
from json import dumps
from mimetypes import guess_extension
from pathlib import Path
from typing import Any, Literal, TypeVar
from urllib.parse import urlparse

from aiohttp import ClientResponseError, ClientSession
from arabot.core import Ara, Cog, Context
from arabot.utils import Category, CustomEmoji, bold, dsafe, getkeys, mono
from async_lru import alru_cache
from disnake import Embed, File
from disnake.ext import commands, tasks
from disnake.utils import find


class Google(
    Cog,
    category=Category.LOOKUP,
    keys={"g_search_key", "g_isearch_key", "g_cse", "g_yt_key", "g_tts_key"},
):
    def __init__(self, ara: Ara):
        self.ara = ara

    @commands.command(aliases=["i", "img"], brief="Top search result from Google Images")
    async def image(self, ctx: Context, *, query):
        await ctx.trigger_typing()
        images_json = await self.ara.session.fetch_json(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": self.g_isearch_key,
                "cx": self.g_cse,
                "q": query + " -filetype:svg",
                "searchType": "image",
            },
        )
        for i in filter(
            lambda item: item.get("mime") != "image/svg+xml"
            and item.get("fileFormat") != "image/svg+xml",
            images_json.get("items", ()),
        ):
            image_url = i["link"]
            try:
                async with self.ara.session.get(image_url) as r:
                    if not r.ok or r.content_type == "image/svg+xml":
                        continue
                    image = BytesIO(await r.read())
                fn = Path(
                    getattr(r.content_disposition, "filename", urlparse(image_url)[2]) or "image"
                ).stem
                ext = guess_extension(r.headers.get("Content-Type", "image/png"), strict=False)
                await ctx.send(file=File(image, fn + ext))
                return
            except Exception as e:
                logging.error(e, "\nFailed image:", image_url)
        await ctx.send("No images found")

    @commands.command(aliases=["g"], brief="Top Google Search result")
    async def google(self, ctx: Context, *, query):
        json = await self.ara.session.fetch_json(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": self.g_search_key,
                "cx": self.g_cse,
                "q": query,
                "num": 1,
            },
        )
        await ctx.send(json["items"][0]["link"] if json["items"] else "No results found")

    @commands.command(aliases=["g3"], brief="Top 3 Google Search results")
    async def google3(self, ctx: Context, *, query):
        json = await self.ara.session.fetch_json(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": self.g_search_key,
                "cx": self.g_cse,
                "q": query,
                "num": 3,
            },
        )
        if not json["items"]:
            await ctx.send("No results found")
            return
        embed = Embed(
            title="Google search results",
            description="Showing top 3 search results",
            url="https://google.com/search?q=" + query,
        )
        for hit in json["items"]:
            embed.add_field(
                name=hit["link"],
                value=f"{bold(hit['title'])}\n{hit['snippet']}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(aliases=["yt"], brief="Top search result from YouTube")
    async def youtube(self, ctx: Context, *, query):
        json = await self.ara.session.fetch_json(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "key": self.g_yt_key,
                "q": query,
                "maxResults": 1,
                "type": "video",
                "regionCode": "US",
            },
        )
        await ctx.send(
            "https://youtu.be/" + json["items"][0]["id"]["videoId"]
            if json["items"]
            else "No videos found"
        )

    @commands.cooldown(5, 60, commands.BucketType.guild)
    @commands.command(brief="Synthesize speech from text")
    async def tts(self, ctx: Context, *, text: str = None):
        if not text:
            await ctx.send("I need text to synthesize")
            return
        await ctx.trigger_typing()
        try:
            lang = await self.ara.session.fetch_json(
                "https://translation.googleapis.com/language/translate/v2/detect",
                params={"key": self.g_tts_key, "q": text},
            )
        except ClientResponseError:
            lang = "en"
        else:
            lang = lang["data"]["detections"][0][0]["language"]
            if lang == "und":
                lang = "en"

        speech = await self.ara.session.fetch_json(
            "https://texttospeech.googleapis.com/v1/text:synthesize",
            method="post",
            params={"key": self.g_tts_key},
            data=dumps(
                {
                    "input": {"text": text},
                    "voice": {"languageCode": lang},
                    "audioConfig": {"audioEncoding": "OGG_OPUS"},
                }
            ),
        )
        speech = b64decode(speech["audioContent"])
        await ctx.reply(file=File(BytesIO(speech), text + ".ogg"))

    async def cog_command_error(self, ctx: Context, error):
        match error:
            case ClientResponseError(status=status):
                match status:
                    case 429:
                        await ctx.send(
                            f"Sorry, I've hit today's 100 queries/day limit {CustomEmoji.MEISTARE}"
                        )
                    case 403:
                        await ctx.send(
                            f"{mono(ctx.invoked_with)} doesn't work without "
                            f"cloud-billing,\nask `{self.ara.owner}` to enable it."
                        )
            case _:
                raise


Detection = TypeVar("Detection", bound=dict[str, str | bool | float])
LangCodeAndOrName = list[str]


class TranslationClient:
    BASE = "https://translation.googleapis.com/language/translate/v2"

    def __init__(self, key: str, session: ClientSession | None = None):
        self.key = key
        self.session = session or ClientSession()
        self._invalidate_language_cache.start()

    async def _api(self, method: str, **params: dict[str, Any]) -> dict[str, Any]:
        return await self.session.fetch_json(
            f"{self.BASE}/{method.strip('/')}", params={"key": self.key, **params}
        )

    async def translate(
        self,
        text: str,
        target: str,
        source: str | None = None,
        format: Literal["text", "html"] = "text",
    ) -> tuple[str, str | None]:
        data = await self._api(
            "/",
            key=self.key,
            q=text,
            target=target,
            source=source or "",
            format=format,
        )
        translations: list[dict[str, str]] = data["data"]["translations"]
        translation = translations[0]
        translated_text = translation["translatedText"]
        detected_source_language = translation.get("detectedSourceLanguage")
        return translated_text, detected_source_language

    async def detect(self, text: str) -> Detection:
        data = await self._api("/detect", q=text)
        detections: list[Detection] = data["data"]["detections"]
        return detections[0]

    @alru_cache(maxsize=1, cache_exceptions=False)
    async def languages(self, target: str | None = None) -> list[LangCodeAndOrName]:
        data = await self._api("/languages", target=target or "")
        languages: list[dict[str, str]] = data["data"]["languages"]
        return [list(lang.values()) for lang in languages]

    @tasks.loop(time=datetime.time())
    async def _invalidate_language_cache(self):
        self.languages.cache_clear()


class Translate(Cog, category=Category.LOOKUP):
    default_target = ["en", "English"]

    def __init__(self, trans_client: TranslationClient):
        self.gtrans = trans_client

    @commands.command(aliases=["tr", "trans"], brief="Translates text")
    async def translate(self, ctx: Context, *query):
        if not query:
            await ctx.reply("I need text to translate!")
            return

        all_langs = await self.gtrans.languages(target=self.default_target[0])
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

                if source := find_lang(source):
                    if temp := find_lang(target):
                        target = temp
                    else:
                        text = f"{target} {text}"
                        target = source
                        source = None
                else:
                    text = f"{source} {target} {text}"
                    target = self.default_target
                    source = None

            case [target, text]:
                source = None

                if temp := find_lang(target):
                    target = temp
                else:
                    text = f"{target} {text}"
                    target = self.default_target

            case [text]:
                target = self.default_target
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


def setup(ara: Ara):
    ara.add_cog(Google(ara))

    trans_client = TranslationClient(getkeys("g_trans_key")[0], ara.session)
    ara.add_cog(Translate(trans_client))
