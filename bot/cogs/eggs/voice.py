from discord.ext.commands import Cog
from .._utils import isValid
import discord
import asyncio
from sys import _getframe

class Voice(Cog, name="Eggs"):
	def __init__(self, client):
		self.bot = client

	async def VoiceReaction(self, msg, vorbis, trigger=None):
		if isValid(self.bot, msg,
			_getframe(1).f_code.co_name.replace("_", " ")
			if trigger is None else trigger) and (await self.bot.get_context(msg)).voice_client is None:
			for channel in msg.guild.voice_channels:
				if channel.members:
					(vc := await channel.connect()).play(
						await discord.FFmpegOpusAudio.from_probe(f"./bot/res/ogg/{vorbis}.ogg"),
						after=lambda e: vc.loop.create_task(vc.disconnect())
					)
					break

	@Cog.listener("on_message")
	async def lewd(self, msg):
		await self.VoiceReaction(msg, "aroro")

	@Cog.listener("on_message")
	async def tuna(self, msg):
		await self.VoiceReaction(msg, "nekocharm")

	@Cog.listener("on_message")
	async def gnome(self, msg):
		await self.VoiceReaction(msg, "gnome")

	@Cog.listener("on_message")
	async def teri(self, msg):
		await self.VoiceReaction(msg, "teri")

	def cog_unload(self):
		for c in self.bot.voice_clients:
			c.loop.create_task(c.disconnect())

def setup(client):
	client.add_cog(Voice(client))