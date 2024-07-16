import datetime
from base64 import b64decode
from io import BytesIO

from aiohttp import ClientSession
from async_lru import alru_cache
from disnake import File, PCMAudio
from disnake.ext import tasks
from disnake.ext.commands import clean_content, command

from arabot.core import Category, Cog, Context
from arabot.utils import CUSTOM_EMOJI_RE


class GoogleTTS(Cog, category=Category.GENERAL, keys={"G_TTS_KEY"}):
    G_TTS_KEY: str

    def __init__(self, session: ClientSession):
        self.session = session
        self._invalidate_voices_cache.start()

    @command(aliases=["synth"], brief="Synthesize speech from text", usage="[lang] <text or reply>")
    async def tts(self, ctx: Context):
        async with ctx.typing():
            if pcm := await self.parse_check_detect_synthesize(ctx):
                await ctx.reply(file=File(pcm, "audio.wav"))

    @command(
        aliases=["pronounce"],
        brief="Pronounce text in voice channel",
        usage="[lang] <text or reply>",
    )
    async def speak(self, ctx: Context):
        if ctx.guild.voice_client:
            await ctx.send_("busy")
            return
        if not getattr(ctx.author.voice, "channel", None):
            await ctx.send_("not_connected")
            return

        async with ctx.typing():
            if pcm := await self.parse_check_detect_synthesize(ctx):
                await ctx.author.voice.channel.connect_play_disconnect(PCMAudio(pcm))
                await ctx.tick()

    async def parse_check_detect_synthesize(self, ctx: Context) -> BytesIO | None:
        langs = await self.voices()
        lang, text = self.parse_query(ctx.argument_only, langs)

        if not text and not (text := await ctx.rsearch(ctx.RSearchTarget.CONTENT)):
            await ctx.send_("provide_text")
            return None
        text = await clean_content(fix_channel_mentions=True).convert(ctx, text)
        text = CUSTOM_EMOJI_RE.sub(r";\g<name>;", text)

        if not lang:
            lang = await self.detect_language(text)
            if not self.find_lang(lang, langs):
                await ctx.send_("unknown_language")
                return None

        audio = await self.synthesize(text, lang, "LINEAR16")
        return BytesIO(audio)

    def parse_query(self, query: str, langs: list[dict]) -> tuple[str | None, str | None]:
        match query.split(maxsplit=1):
            case []:
                lang = text = None
            case [str1]:
                text = None if (lang := self.find_lang(str1, langs)) else str1
            case [str1, str2]:
                text = str2 if (lang := self.find_lang(str1, langs)) else f"{str1} {str2}"
        return lang, text

    @staticmethod
    def find_lang(string: str, langs: list[dict[str, list[str]]]) -> str | None:
        if not string:
            return None
        for lng in langs:
            if (lang := lng["languageCodes"][0].split("-")[0]) == string.lower():
                return lang
        return None

    async def synthesize(self, text: str, lang: str, encoding: str) -> bytes:
        data = await self.session.fetch_json(
            "https://texttospeech.googleapis.com/v1/text:synthesize",
            method="post",
            params={"key": self.G_TTS_KEY},
            json={
                "input": {"text": text},
                "voice": {"languageCode": lang},
                "audioConfig": {
                    "audioEncoding": encoding,
                    "sampleRateHertz": 96000,  # Somehow fixes high-pitched voice
                },
            },
        )
        return b64decode(data["audioContent"])

    @alru_cache
    async def voices(self, language_code: str | None = None) -> list[dict]:
        data: dict[str, list[dict]] = await self.session.fetch_json(
            "https://texttospeech.googleapis.com/v1/voices",
            params={"key": self.G_TTS_KEY, "languageCode": language_code or ""},
        )
        return data["voices"]

    async def detect_language(self, text: str) -> str | None:
        data: dict[str, dict[str, list[list[dict]]]] = await self.session.fetch_json(
            "https://translation.googleapis.com/language/translate/v2/detect",
            params={"key": self.G_TTS_KEY, "q": text},
        )
        lang = data["data"]["detections"][0][0]["language"]
        return lang if lang != "und" else None

    @tasks.loop(time=datetime.time())
    async def _invalidate_voices_cache(self) -> None:
        self.voices.cache_clear()
