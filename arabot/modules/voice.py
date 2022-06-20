import re
from os import listdir
from random import choice

import disnake
from arabot.core import Ara, Cog, pfxless
from arabot.utils import (
    author_in_voice_channel,
    bot_not_speaking_in_guild,
    can_someone_hear_in_author_channel,
)


class Voice(Cog):
    def __init__(self, ara: Ara):
        self.ara = ara

    MISC_OGG_DIR = "resources/ogg/misc"
    MISC_OGG_REGEX = rf"\b{'|'.join(re.escape(f[:-4]) for f in listdir(MISC_OGG_DIR))}\b"
    GACHI_OGG_DIR = "resources/ogg/gachi"
    GACHI_OGG_FILES = listdir(GACHI_OGG_DIR)

    @can_someone_hear_in_author_channel
    @author_in_voice_channel
    @bot_not_speaking_in_guild
    @pfxless(regex=MISC_OGG_REGEX)
    async def misc_voice(self, msg: disnake.Message):
        filename = re.search(self.MISC_OGG_REGEX, msg.content, re.IGNORECASE)[0] + ".ogg"
        audio = disnake.FFmpegOpusAudio(f"{self.MISC_OGG_DIR}/{filename.lower()}")
        await msg.author.voice.channel.connect_play_disconnect(audio)

    @can_someone_hear_in_author_channel
    @author_in_voice_channel
    @bot_not_speaking_in_guild
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
