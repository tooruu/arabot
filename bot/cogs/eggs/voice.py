from os import listdir
from discord.ext.commands import Cog
from .._utils import is_valid
import discord

class Voice(Cog, name="Eggs"):
	def __init__(self, client):
		self.bot = client
		self.OGGDIR = "./bot/res/ogg"

	@Cog.listener("on_message")
	async def voice_reaction(self, msg):
		if (await self.bot.get_context(msg)).voice_client is None:
			for s in (fname[:-4] for fname in listdir(self.OGGDIR)):
				if is_valid(self.bot, msg, f"\\b{s}\\b"):
					for channel in msg.guild.voice_channels:
						if channel.members:
							(vc := await channel.connect()).play(
								await discord.FFmpegOpusAudio.from_probe(f"{self.OGGDIR}/{s}.ogg"),
								after=lambda e: vc.loop.create_task(vc.disconnect())
							)
							return

	def cog_unload(self):
		for c in self.bot.voice_clients:
			c.loop.create_task(c.disconnect())

def setup(client):
	client.add_cog(Voice(client))