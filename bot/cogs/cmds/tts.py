from base64 import b64decode
from io import BytesIO
from json import dumps
from discord import File
from discord.ext.commands import command, Cog, cooldown, BucketType
from ...helpers.auth import req_auth


class TTS(Cog, name="Commands"):
    def __init__(self, client, key):
        self.bot = client
        self.key = key

    @cooldown(5, 60, BucketType.guild)
    @command(name="tts", brief="<text> | Synthesize speech from text")
    async def synthesize(self, ctx, *, text=None):
        if not text:
            await ctx.send("I need text to synthesize")
            return
        async with ctx.typing():
            async with self.bot.ses.post(
                "https://translation.googleapis.com/language/translate/v2/detect", params={"key": self.key, "q": text}
            ) as lang:
                if lang.status == 200:
                    lang = (await lang.json())["data"]["detections"][0][0]["language"]
                    if lang == "und":
                        lang = "en"
                else:
                    lang = "en"

            async with self.bot.ses.post(
                "https://texttospeech.googleapis.com/v1beta1/text:synthesize",
                params={
                    "key": self.key,
                },
                data=dumps(
                    {
                        "input": {"text": text},
                        "voice": {"languageCode": lang},
                        "audioConfig": {
                            "audioEncoding": "OGG_OPUS",
                        },
                    }
                ),
            ) as tts:
                if tts.status != 200:
                    await ctx.send("An error occurred")
                    return
                tts = b64decode((await tts.json())["audioContent"])
            await ctx.reply(file=File(BytesIO(tts), text + ".ogg"))


@req_auth("g_tts_key")
def setup(client, key):
    client.add_cog(TTS(client, key))
