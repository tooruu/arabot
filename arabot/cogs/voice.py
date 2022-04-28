import re
from os import listdir
from random import choice

import disnake
from arabot.core import Ara, Cog, pfxless
from disnake.ext.commands import check


class Voice(Cog):
    def __init__(self, ara: Ara):
        self.ara = ara

    MISC_OGG_DIR = "resources/ogg/misc"
    MISC_OGG_REGEX = rf"\b{'|'.join(re.escape(f[:-4]) for f in listdir(MISC_OGG_DIR))}\b"
    GACHI_OGG_DIR = "resources/ogg/gachi"
    GACHI_OGG_FILES = listdir(GACHI_OGG_DIR)

    @check(
        lambda msg: not all(
            m.bot or m.voice.deaf or m.voice.self_deaf for m in msg.author.voice.channel.members
        )
    )
    @check(lambda msg: getattr(msg.author.voice, "channel", None))
    @check(lambda msg: not msg.guild.voice_client)
    @pfxless(regex=MISC_OGG_REGEX)
    async def misc_voice(self, msg: disnake.Message):
        filename = re.search(self.MISC_OGG_REGEX, msg.content, re.IGNORECASE).group() + ".ogg"
        audio = disnake.FFmpegOpusAudio(f"{self.MISC_OGG_DIR}/{filename.lower()}")
        await msg.author.voice.channel.connect_play_disconnect(audio)

    @check(
        lambda msg: not all(
            m.bot or m.voice.deaf or m.voice.self_deaf for m in msg.author.voice.channel.members
        )
    )
    @check(lambda msg: getattr(msg.author.voice, "channel", None))
    @check(lambda msg: not msg.guild.voice_client)
    @pfxless()
    async def gachi(self, msg: disnake.Message):
        filename = choice(self.GACHI_OGG_FILES)
        audio = disnake.FFmpegOpusAudio(f"{self.GACHI_OGG_DIR}/{filename}")
        await msg.author.voice.channel.connect_play_disconnect(audio)


def setup(ara: Ara):
    ara.add_cog(Voice(ara))


def teardown(ara: Ara):
    for vc in ara.voice_clients:
        vc.loop.create_task(vc.disconnect(force=True))
