from discord.ext.commands import Cog #, command
from discord.ext.commands.Cog import listener
from ..utils import isValid
import discord
import asyncio


class EasterEggs(Cog):
	def __init__(self, client):
		self.bot = client

	@listener("on_message")
	async def communism(self, msg):
		if isValid(self.bot, msg, "communism"):
			await msg.channel.send(
				""":b::b::b::b::b::b::b::b::b::b::b::b::b::b::b:
:b::b::b::b::b::b::b::b:<:CommuThink:676973669796544542>:b::b::b::b::b::b:
:b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b::b:
:b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b:
:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:"""
			)
			await msg.channel.send(
				"""
:b::b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:
:b::b::b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:
:b::b::b::b:<:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b::b::b::b::b::b::b::b::b::b::b::b::b::b:"""
			)

	@listener("on_message")
	async def lewd(self, msg):
		if isValid(self.bot, msg, "lewd") and (await self.bot.get_context(msg)).voice_client is None:
			for channel in msg.guild.voice_channels:
				if channel.members:
					channel = await channel.connect()
					channel.play(
						await discord.FFmpegOpusAudio.from_probe("aroro.ogg"),
						after=lambda e: asyncio.run_coroutine_threadsafe(channel.disconnect(), self.bot.loop).result()
					)
					break

	@listener("on_message")
	async def za_warudo(self, msg):
		if isValid(self.bot, msg, "za warudo"):
			await msg.channel.set_permissions(msg.guild.default_role, send_messages=False)
			await msg.channel.send("<:KonoDioDa:676949860502732803>")
			await msg.channel.send("***Toki yo tomare!***")
			for i in ("Ichi", "Ni", "San", "Yon", "Go"): # Ichi Ni San Yon Go Roku Nana Hachi Kyu
				await asyncio.sleep(2)
				await msg.channel.send(content=f"*{i} byou keika*")
			await asyncio.sleep(1)
			await msg.channel.send("Toki wa ugoki dasu")
			await asyncio.sleep(2)
			await msg.channel.purge(limit=8)
			await msg.channel.set_permissions(msg.guild.default_role, overwrite=None)


def setup(client):
	client.add_cog(EasterEggs(client))