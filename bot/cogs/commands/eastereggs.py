from discord.ext.commands import Cog #, command
from .._utils import isValid
import discord
import asyncio
from sys import _getframe
from re import search

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
	async def za_warudo(self, msg):
		if isValid(self.bot, msg, "za warudo") and self.bot.user:
			old_perms = msg.channel.overwrites_for(msg.guild.default_role)
			temp_perms = msg.channel.overwrites_for(msg.guild.default_role)
			temp_perms.send_messages = False
			print(id(temp_perms) == id(old_perms))
			await msg.channel.set_permissions(msg.guild.default_role, overwrite=temp_perms)
			await msg.channel.send("<:KonoDioDa:676949860502732803>")
			await msg.channel.send("***Toki yo tomare!***")
			for i in ("Ichi", "Ni", "San", "Yon", "Go"): # Ichi Ni San Yon Go Roku Nana Hachi Kyu
				await asyncio.sleep(2)
				await msg.channel.send(content=f"*{i} byou keika*")
			await asyncio.sleep(1)
			await msg.channel.send("Toki wa ugoki dasu")
			await asyncio.sleep(2)
			await msg.channel.purge(limit=7)
			await msg.channel.set_permissions(msg.guild.default_role, overwrite=old_perms)

	@Cog.listener("on_message")
	async def lewd(self, msg):
		await self.VoiceReaction(msg, "aroro")

	@Cog.listener("on_message")
	async def tuna(self, msg):
		await self.VoiceReaction(msg, "nekocharm")

	@Cog.listener("on_message")
	async def teri(self, msg):
		await self.VoiceReaction(msg, "teri")

	# TODO: toggleable per-server
	#@Cog.listener("on_message")
	#async def everyone(self, msg):
	#	if msg.mention_everyone:
	#		await msg.delete()

	@Cog.listener("on_message")
	async def gaygames(self, msg):
		if not msg.content.startswith(
			self.bot.command_prefix
		) and msg.author != self.bot.user and msg.guild.id == 433298614564159488:
			for gaygame in (
				"кс",
				"cs",
				"мм",
				"mm",
				"рафт",
				"raft",
				"фортнайт",
				"fortnite"
				"раст",
				"rust",
				"osu",
				"осу",
				"destiny",
				"дестини",
				"дестени",
			):
				if search(f"\\b{gaygame}\\b", msg.content.lower()):
					await msg.channel.send(f"{gaygame}? Ебать ты гей 🤡, иди в мут нахуй")
					old_perms = msg.channel.overwrites_for(msg.author)
					temp_perms = msg.channel.overwrites_for(msg.author)
					temp_perms.send_messages = False
					await msg.channel.set_permissions(msg.author, overwrite=temp_perms)
					await asyncio.sleep(60)
					await msg.channel.set_permissions(msg.author, overwrite=old_perms)
					break

	@Cog.listener("on_message")
	async def shine(self, msg):
		if "shine" in msg.content.lower():
			await msg.channel.send("no u")

	@Cog.listener("on_message")
	async def urban_listener(self, msg):
		if regex := search(r"(?:wh?[ao]t|nani)'?\s?i?s\s(.[^?]+)", msg.content.lower()):
			await self.bot.get_command("urban")(await self.bot.get_context(msg), term=regex.group(1))

def setup(client):
	client.add_cog(EasterEggs(client))
