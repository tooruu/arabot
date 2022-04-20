from base64 import b64decode
from io import BytesIO

from aiohttp import ClientResponseError
from arabot.core import Ara, Category, Cog, Context
from disnake import File, PCMAudio
from disnake.ext.commands import BucketType, command, cooldown


class TextToSpeech(Cog, category=Category.GENERAL, keys={"g_tts_key"}):
    DEFAULT_LANGUAGE = "en"

    def __init__(self, ara: Ara):
        self.ara = ara

    @command(aliases=["synth"], brief="Synthesize speech from text")
    @cooldown(5, 60, BucketType.guild)
    async def tts(self, ctx: Context, *, text: str = None):
        if not text:
            await ctx.send("I need text to synthesize")
            return

        async with ctx.typing():
            ogg = await self.text_to_audio(text)
            await ctx.reply(file=File(ogg, text + ".ogg"))

    @command(aliases=["pronounce"], brief="Pronounce text in voice channel")
    @cooldown(5, 60, BucketType.guild)
    async def speak(self, ctx: Context, *, text: str = None):
        if not text:
            await ctx.send("I need text to pronounce")
            return
        if ctx.guild.voice_client:
            await ctx.send("I'm already speaking")
            return
        if not getattr(ctx.author.voice, "channel", None):
            await ctx.send("You're not connected to a voice channel")
            return

        pcm = await self.text_to_audio(text, "LINEAR16")
        await ctx.author.voice.channel.connect_play_disconnect(PCMAudio(pcm))

    async def text_to_audio(self, text: str, encoding="OGG_OPUS") -> BytesIO:
        lang = await self.detect_language(text) or self.DEFAULT_LANGUAGE
        audio = await self.synthesize(text, lang, encoding)
        return BytesIO(audio)

    async def synthesize(self, text: str, lang=DEFAULT_LANGUAGE, encoding="OGG_OPUS") -> bytes:
        data = await self.ara.session.fetch_json(
            "https://texttospeech.googleapis.com/v1/text:synthesize",
            method="post",
            params={"key": self.g_tts_key},
            json={
                "input": {"text": text},
                "voice": {"languageCode": lang},
                "audioConfig": {
                    "audioEncoding": encoding,
                    "sampleRateHertz": 96000,  # idk why but this works for both ;tts and ;speak
                },
            },
        )
        return b64decode(data["audioContent"])

    async def detect_language(self, text: str) -> str | None:
        try:
            data: dict[str, dict[str, list[list[dict]]]] = await self.ara.session.fetch_json(
                "https://translation.googleapis.com/language/translate/v2/detect",
                params={"key": self.g_tts_key, "q": text},
            )
        except ClientResponseError:
            return None
        else:
            lang = data["data"]["detections"][0][0]["language"]
            return lang if lang != "und" else None
