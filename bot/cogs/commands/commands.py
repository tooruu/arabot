from discord.ext.commands import command, Cog, check, has_permissions, group, errors
from .._utils import *
import discord

# sauce
from aiohttp import ClientSession as WebSession
from jikanpy import AioJikan
from urllib.parse import quote
from io import BytesIO


class Commands(Cog):
	def __init__(self, client):
		self.bot = client

	@command()
	async def ping(self, ctx):
		await ctx.send(f":ping_pong: Pong after {round(self.bot.latency, 3)}ms!")

	@command()
	async def love(self, ctx, partner: FindMember):
		await ctx.send(f"{ctx.author.mention} loves {partner.mention} :heart:" if partner else f"Love partner not found")

	@command(aliases=["exit", "quit"])
	@check(isDev)
	async def stop(self, ctx):
		await ctx.send("Stopping!")
		print("Stopping!")
		await self.bot.close()

	@command()
	@has_permissions(manage_guild=True)
	async def rename(self, ctx, chan: discord.TextChannel, *, name):
		oldName = chan.name
		await chan.edit(name=name)
		await ctx.send(f"Renamed **{oldName}** to **{chan.name}**")

	@command()
	@check(isDev)
	async def status(self, ctx, _type: int, *, name):
		if _type not in (0, 1, 2, 3):
			return
		await setPresence(self.bot, _type, name)

	@command(name="177013")
	async def _177013(self, ctx):
		await setPresence(self.bot, 3, "177013 with yo mama")

	@command(aliases=["sauce"]) # response = trace.moe, sauce = MAL
	async def source(self, ctx, image_url=None):
		image_url = ctx.message.attachments[0].url if ctx.message.attachments else image_url
		if image_url is not None:
			async with WebSession(loop=self.bot.loop) as session:
				async with session.get("https://trace.moe/api/search", params={"url": image_url}) as response:
					response = (await response.json())["docs"][0]
					sauce = (await AioJikan(session=session).anime(response["mal_id"]))
				async with session.get(
					"https://trace.moe/preview.php",
					params={
					"anilist_id": response['anilist_id'],
					"file": quote(response['filename']),
					"t": str(response['at']),
					"token": response['tokenthumb']
					}
				) as preview:
					preview = await preview.read()
			embed = discord.Embed(
				color=32767,
				description=f"Similarity: {response['similarity']:.1%} | Score: {sauce['score']} | {sauce['status']}"
			)
			embed.set_author(name=sauce["title"], url=sauce["url"])
			embed.set_thumbnail(url=sauce["image_url"])
			sauce["synopsis"] = sauce["synopsis"].partition(" [")[0]
			embed.add_field(
				name="Synopsis",
				value=sauce["synopsis"]
				if len(sauce["synopsis"]) <= 600 else ".".join(sauce["synopsis"][:600].split(".")[0:-1]) + "..."
			)
			embed.set_footer(
				text=f"Requested by {ctx.author.nick} | Powered by trace.moe", icon_url=str(ctx.author.avatar_url)
			)
			await ctx.send(
				f"*Episode {response['episode']} ({int(response['at']/60)}:{int(response['at']%60)})*",
				file=discord.File(BytesIO(preview), response["filename"]),
				embed=embed
			)

	@group(aliases=["cogs"], invoke_without_command=True)
	@check(isDev)
	async def cog(self, ctx):
		await ctx.send("Loaded cogs: " + ", ".join(f"**{c}**" for c in self.bot.cogs.keys()))

	@cog.command(aliases=["add"])
	async def load(self, ctx, *cogs):
		loaded = []
		for i in cogs:
			try:
				self.bot.load_extension(f"cogs.{i}")
				loaded.append(f"**{i}**")
			except errors.ExtensionNotFound:
				await ctx.send(f"**{i}** was not found")
			except errors.ExtensionAlreadyLoaded:
				await ctx.send(f"**{i}** is already loaded")
			except (errors.ExtensionFailed, errors.NoEntryPointError):
				await ctx.send(f"**{i}** is an invalid extension")
		await ctx.send("Loaded " + (", ".join(loaded) or "nothing"))

	@cog.command(aliases=["remove"])
	async def unload(self, ctx, *cogs):
		unloaded = []
		for i in cogs:
			try:
				self.bot.unload_extension(f"cogs.{i}")
				unloaded.append(f"**{i}**")
			except errors.ExtensionNotLoaded:
				pass
		await ctx.send("Unloaded " + (", ".join(unloaded) or "nothing"))

	@cog.command()
	async def reload(self, ctx, *cogs):
		reloaded = []
		for i in cogs:
			try:
				self.bot.reload_extension(f"cogs.{i}")
				reloaded.append(f"**{i}**")
			except errors.ExtensionNotFound:
				await ctx.send(f"**{i}** was not found")
			except errors.ExtensionNotLoaded:
				self.bot.load_extension(f"cogs.{i}")
				reloaded.append(f"**{i}**")
			except (errors.ExtensionFailed, errors.NoEntryPointError):
				await ctx.send(f"**{i}** is an invalid extension")
		await ctx.send("Reloaded " + (", ".join(reloaded) or "nothing"))

	@command(aliases=["purge", "prune", "d"])
	@has_permissions(manage_messages=True)
	async def clear(self, ctx, amount: int = None):
		if amount is not None:
			await ctx.channel.purge(limit=amount + 1)
		else:
			await ctx.message.delete()

	@command(aliases=["a"])
	async def avatar(self, ctx, target: FindMember):
		await ctx.send(
			file=discord.
			File(BytesIO(await target.avatar_url_as(static_format="png").read()),
			str(target.avatar_url).split("/")[-1]) if target else "User not found"
		)

	@command(aliases=["emote", "e"])
	async def emoji(self, ctx, emoji: FindEmoji):
		await ctx.message.delete()
		await ctx.send(
			file=discord.File(BytesIO(await emoji.url.read()),
			str(emoji.url).split("/")[-1]) if emoji else "Emoji not found"
		)

	@command()
	async def call(self, ctx, target: MemberConverter): # Not use smart lookup
		if target is not None:
			if target.dm_channel is None:
				await target.create_dm()
			await target.dm_channel.send(f"{ctx.author.mention} wants you to show up in **{ctx.guild.name}**.")
			await ctx.send(f"Called {target.mention} to show up")
		else:
			await ctx.send("User not found")

	@command()
	async def inspire(self, ctx):
		async with WebSession(loop=self.bot.loop) as session:
			async with session.get("https://inspirobot.me/api", params={"generate": "true"}) as url:
				url = (await url.read()).decode()
				async with session.get(url) as img:
					await ctx.send(file=discord.File(BytesIO(await img.read()), url.split("/")[-1]))


def setup(client):
	client.add_cog(Commands(client))