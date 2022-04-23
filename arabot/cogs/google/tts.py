import datetime
from base64 import b64decode
from io import BytesIO

from arabot.core import Ara, Category, Cog, Context
from async_lru import alru_cache
from disnake import File, PCMAudio
from disnake.ext import tasks
from disnake.ext.commands import BucketType, command, cooldown
from disnake.utils import find


class TextToSpeech(Cog, category=Category.GENERAL, keys={"g_tts_key"}):
    def __init__(self, ara: Ara):
        self.ara = ara
        self._invalidate_voices_cache.start()

    @command(aliases=["synth"], brief="Synthesize speech from text")
    @cooldown(5, 60, BucketType.guild)
    async def tts(self, ctx: Context, *query):
        async with ctx.typing():
            if pcm := await self.parse_check_detect_synthesize(ctx, query):
                await ctx.reply(file=File(pcm, "audio.wav"))

    @command(aliases=["pronounce"], brief="Pronounce text in voice channel")
    @cooldown(5, 60, BucketType.guild)
    async def speak(self, ctx: Context, *query):
        if ctx.guild.voice_client:
            await ctx.send("I'm already speaking")
            return
        if not getattr(ctx.author.voice, "channel", None):
            await ctx.send("You're not connected to a voice channel")
            return

        async with ctx.typing():
            if pcm := await self.parse_check_detect_synthesize(ctx, query):
                await ctx.author.voice.channel.connect_play_disconnect(PCMAudio(pcm))

    async def parse_check_detect_synthesize(self, ctx: Context, query: list[str]) -> BytesIO | None:
        langs = await self.voices()
        lang, text = self.parse_query(query, langs)

        ctx.message.content = ""
        if not text and not (text := await ctx.message.rsearch(ctx, "content")):
            await ctx.send("I need text to pronounce")
            return

        if not lang and not self.find_lang(lang := await self.detect_language(text), langs):
            await ctx.send("Couldn't detect language")
            return

        audio = await self.synthesize(text, lang, "LINEAR16")
        return BytesIO(audio)

    def parse_query(self, query: str, langs: list[dict]) -> tuple[str | None, str | None]:
        match query:
            case []:
                lang = None
                text = None

            case [text]:
                if self.find_lang(text, langs):
                    lang = text
                    text = None
                else:
                    lang = None

            case [lang, *text]:
                text = " ".join(text)
                if not self.find_lang(lang, langs):
                    text = f"{lang} {text}"
                    lang = None

        return lang, text

    @staticmethod
    def find_lang(string: str, langs: list[dict[str, list[str]]]) -> str | None:
        if not string:
            return None
        return find(lambda lng: lng["languageCodes"][0].split("-")[0] == string.lower(), langs)

    async def synthesize(self, text: str, lang: str, encoding: str) -> bytes:
        data = await self.ara.session.fetch_json(
            "https://texttospeech.googleapis.com/v1/text:synthesize",
            method="post",
            params={"key": self.g_tts_key},
            json={
                "input": {"text": text},
                "voice": {"languageCode": lang},
                "audioConfig": {
                    "audioEncoding": encoding,
                    "sampleRateHertz": 96000,  # somehow fixes high-pitched voice
                },
            },
        )
        return b64decode(data["audioContent"])

    @alru_cache(cache_exceptions=False)
    async def voices(self, language_code: str | None = None) -> list[dict]:
        data: dict[str, list[dict]] = await self.ara.session.fetch_json(
            "https://texttospeech.googleapis.com/v1/voices",
            params={"key": self.g_tts_key, "languageCode": language_code or ""},
        )
        return data["voices"]

    async def detect_language(self, text: str) -> str | None:
        data: dict[str, dict[str, list[list[dict]]]] = await self.ara.session.fetch_json(
            "https://translation.googleapis.com/language/translate/v2/detect",
            params={"key": self.g_tts_key, "q": text},
        )
        lang = data["data"]["detections"][0][0]["language"]
        return lang if lang != "und" else None

    @tasks.loop(time=datetime.time())
    async def _invalidate_voices_cache(self):
        self.voices.cache_clear()
