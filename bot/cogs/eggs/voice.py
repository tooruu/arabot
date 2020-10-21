from discord.ext.commands import Cog
from .._utils import is_valid
import discord
import asyncio
from sys import _getframe

class Voice(Cog, name="Eggs"):
	def __init__(self, client):
		self.bot = client

	async def voice_reaction(self, msg, vorbis, trigger=None):
		if is_valid(self.bot, msg, trigger
		if trigger else "\\b{}\\b".format(_getframe(1).f_code.co_name.replace("_", " "))
		) and (await self.bot.get_context(msg)).voice_client is None:
			for channel in msg.guild.voice_channels:
				if channel.members:
					(vc := await channel.connect()).play(
						await discord.FFmpegOpusAudio.from_probe(f"./bot/res/ogg/{vorbis}.ogg"),
						after=lambda e: vc.loop.create_task(vc.disconnect())
					)
					break

	@Cog.listener("on_message")
	async def lewd(self, msg):
		await self.voice_reaction(msg, "aroro")

	@Cog.listener("on_message")
	async def tuna(self, msg):
		await self.voice_reaction(msg, "nekocharm")

	@Cog.listener("on_message")
	async def gnome(self, msg):
		await self.voice_reaction(msg, "gnome")

	@Cog.listener("on_message")
	async def teri(self, msg):
		await self.voice_reaction(msg, "teri")

	@Cog.listener("on_message")
	async def boo(self, msg):
		await self.voice_reaction(msg, "bababooey")

	@Cog.listener("on_message")
	async def paimon(self, msg):
		await self.voice_reaction(msg, "ehe")

	@Cog.listener("on_message")
	async def jugemu(self, msg):
		await self.voice_reaction(msg, "jugemu")

	def cog_unload(self):
		for c in self.bot.voice_clients:
			c.loop.create_task(c.disconnect())

def setup(client):
	client.add_cog(Voice(client))