import datetime
from typing import Any, Literal

from aiohttp import ClientSession
from async_lru import alru_cache
from disnake.ext import tasks

LangCodeAndOrName = list[str]


class TranslationClient:
    BASE_URL = "https://translation.googleapis.com/language/translate/v2"

    def __init__(self, key: str, session: ClientSession):
        self.key = key
        self.session = session
        self._invalidate_language_cache.start()

    async def _api(self, method: str, **params: dict[str, Any]) -> dict[str, Any]:
        return await self.session.fetch_json(
            f"{self.BASE_URL}/{method.strip('/')}", params={"key": self.key} | params
        )

    async def translate(
        self,
        text: str,
        target: str,
        source: str | None = None,
        format_: Literal["text", "html"] = "text",
    ) -> tuple[str, str | None]:
        data = await self._api(
            "/",
            key=self.key,
            q=text,
            target=target,
            source=source or "",
            format=format_,
        )
        translation: dict[str, str] = data["data"]["translations"][0]
        translated_text = translation["translatedText"]
        detected_source_language = translation.get("detectedSourceLanguage")
        return translated_text, detected_source_language

    async def detect(self, text: str) -> str:
        data = await self._api("/detect", q=text)
        detections: list[list[dict[str, str]]] = data["data"]["detections"]
        lang = detections[0][0]["language"]
        return lang if lang != "und" else None

    @alru_cache
    async def languages(self, repr_lang: str | None = None) -> list[LangCodeAndOrName]:
        data = await self._api("/languages", target=repr_lang or "")
        languages: list[dict[str, str]] = data["data"]["languages"]
        return [list(lang.values()) for lang in languages]

    @tasks.loop(time=datetime.time())
    async def _invalidate_language_cache(self) -> None:
        self.languages.cache_clear()
