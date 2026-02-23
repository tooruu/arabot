from disnake.ext.commands import command
from elevenlabs import AsyncElevenLabs
from pyscribe import atranscribe

from arabot.core import Ara, Category, Cog, Context


class Transcription(Cog, category=Category.GENERAL, keys={"ELEVENLABS_API_KEY"}):
    ELEVENLABS_API_KEY: str

    def __init__(self, ara: Ara):
        self.ara = ara
        self.client = AsyncElevenLabs(api_key=self.ELEVENLABS_API_KEY)

    @command(aliases=["stt"], brief="Transcribe audio", usage="<audio>")
    async def transcribe(self, ctx: Context):
        await ctx.trigger_typing()
        audio_url = await ctx.rsearch(ctx.RSearchTarget.AUDIO_VIDEO_URL)

        if not audio_url:
            await ctx.send_("audio_not_found")
            return

        text = await atranscribe(self.client, audio_url)
        await ctx.reply(text)


def setup(ara: Ara):
    ara.add_cog(Transcription(ara))
