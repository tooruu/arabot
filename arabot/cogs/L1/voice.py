import logging
import re
from os import listdir
from random import choice

import disnake
from arabot.core import Ara, Cog, pfxless
from disnake.ext.commands import check


class Voice(Cog):
    MISC_OGG_DIR = "resources/ogg/misc"
    MISC_OGG_REGEX = r"(?<![:\w])({})(?![:\w])".format(
        "|".join(re.escape(f[:-4]) for f in listdir(MISC_OGG_DIR))
    )
    GACHI_OGG_DIR = "resources/ogg/gachi"

    def __init__(self, ara: Ara):
        self.ara = ara

    @check(lambda msg: not msg.guild.voice_client)
    @check(lambda msg: getattr(msg.author.voice, "channel", None))
    @pfxless(regex=MISC_OGG_REGEX)
    async def voice_reaction(self, msg: disnake.Message):
        channel = msg.author.voice.channel

        if not any(not (m.bot or m.voice.deaf or m.voice.self_deaf) for m in channel.members):
            return

        ogg = re.search(self.MISC_OGG_REGEX, msg.content.lower()).group(1)
        audio = await disnake.FFmpegOpusAudio.from_probe(f"{self.MISC_OGG_DIR}/{ogg}.ogg")
        await self.play_ogg(channel, audio)

    @check(lambda msg: not msg.guild.voice_client)
    @check(lambda msg: getattr(msg.author.voice, "channel", None))
    @pfxless(regex=r"(?<![:\w])gachi(?![:\w])")
    async def gachi_reaction(self, msg: disnake.Message):
        channel = msg.author.voice.channel

        if not any(not (m.bot or m.voice.deaf or m.voice.self_deaf) for m in channel.members):
            return

        ogg = choice(listdir(self.GACHI_OGG_DIR))
        audio = await disnake.FFmpegOpusAudio.from_probe(f"{self.GACHI_OGG_DIR}/{ogg}")
        await self.play_ogg(channel, audio)

    @staticmethod
    async def play_ogg(channel: disnake.VoiceChannel, audio: disnake.FFmpegOpusAudio) -> None:
        try:
            vc = await channel.connect()
        except Exception:
            logging.warning(disnake.ClientException("Could not connect to voice channel"))
            return

        disconnect = lambda _: vc.loop.create_task(vc.disconnect())
        vc.play(audio, after=disconnect)

    def cog_unload(self):
        for vc in self.ara.voice_clients:
            vc.loop.create_task(vc.disconnect(force=True))


def setup(ara: Ara):
    ara.add_cog(Voice(ara))
