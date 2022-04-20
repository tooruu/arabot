import re
from os import listdir
from random import choice

import disnake
from arabot.core import Ara, Cog, pfxless
from arabot.utils import opus_from_file
from disnake.ext.commands import check


class Voice(Cog):
    MISC_OGG_DIR = "resources/ogg/misc"
    MISC_OGG_REGEX = r"(?<![:\w])({})(?![:\w])".format(
        "|".join(re.escape(f[:-4]) for f in listdir(MISC_OGG_DIR))
    )
    GACHI_OGG_DIR = "resources/ogg/gachi"
    GACHI_OGG_FILES = listdir(GACHI_OGG_DIR)

    @check(lambda msg: not msg.guild.voice_client)
    @check(lambda msg: getattr(msg.author.voice, "channel", None))
    @pfxless(regex=MISC_OGG_REGEX)
    async def voice_reaction(self, msg: disnake.Message):
        channel = msg.author.voice.channel

        if not any(not (m.bot or m.voice.deaf or m.voice.self_deaf) for m in channel.members):
            return

        ogg = re.search(self.MISC_OGG_REGEX, msg.content.lower()).group(1)
        audio = opus_from_file(f"{self.MISC_OGG_DIR}/{ogg}.ogg")
        await channel.connect_play_disconnect(audio)

    @check(lambda msg: not msg.guild.voice_client)
    @check(lambda msg: getattr(msg.author.voice, "channel", None))
    @pfxless(regex=r"(?<![:\w])gachi(?![:\w])")
    async def gachi_reaction(self, msg: disnake.Message):
        channel = msg.author.voice.channel

        if not any(not (m.bot or m.voice.deaf or m.voice.self_deaf) for m in channel.members):
            return

        ogg = choice(self.GACHI_OGG_FILES)
        audio = opus_from_file(f"{self.GACHI_OGG_DIR}/{ogg}")
        await channel.connect_play_disconnect(audio)


def setup(ara: Ara):
    Voice.ara = ara  # pfxless needs cog.ara to check prefix
    ara.add_cog(Voice())


def teardown(ara: Ara):
    for vc in ara.voice_clients:
        vc.loop.create_task(vc.disconnect(force=True))
