from discord.ext.commands import Cog
from .._utils import isValid
import discord
import asyncio
from sys import _getframe

class EasterEggs(Cog):
	def __init__(self, client):
		self.bot = client

	async def VoiceReaction(self, msg, vorbis, trigger=None):
		if isValid(self.bot, msg,
			_getframe(1).f_code.co_name.replace("_", " ")
			if trigger is None else trigger) and (await self.bot.get_context(msg)).voice_client is None:
			for channel in msg.guild.voice_channels:
				if channel.members:
					(channel := await channel.connect()).play(
						await discord.FFmpegOpusAudio.from_probe(f"./bot/res/{vorbis}.ogg"),
						after=lambda e: asyncio.run_coroutine_threadsafe(channel.disconnect(), self.bot.loop).result()
					)
					break

	@Cog.listener("on_message")
	async def lewd(self, msg):
		await self.VoiceReaction(msg, "aroro")

	@Cog.listener("on_message")
	async def tuna(self, msg):
		await self.VoiceReaction(msg, "nekocharm")

	@Cog.listener("on_message")
	async def teri(self, msg):
		await self.VoiceReaction(msg, "teri")


def setup(client):
	client.add_cog(EasterEggs(client))