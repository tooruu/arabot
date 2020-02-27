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
	@staticmethod
	async def love(ctx, target: FindMember):
		await ctx.send(f"{ctx.author.mention} loves {target.mention} :heart:" if target else f"Love partner not found")

	@command()
	@check(isDev)
	async def stop(self, ctx):
		await ctx.send("Stopping!")
		print("Stopping!")
		await self.bot.close()

	@command()
	@has_permissions(manage_guild=True)
	@staticmethod
	async def rename(ctx, chan: discord.TextChannel, *, name):
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

	@command()
	async def ping(self, ctx):
		await ctx.send(f":ping_pong: Pong after {round(self.bot.latency, 3)}ms!")

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
				file=discord.File(BytesIO(preview), response['filename']),
				embed=embed
			)

	####################################### COG
	@group(aliases=["cogs"])
	@check(isDev)
	async def cog(self, ctx):
		pass

	@cog.command()
	async def load(self, ctx, *cogs):
		for i in cogs:
			try:
				self.bot.load_extension(f"cogs.{i}")
				await ctx.send(f"Loaded **{i}**")
			except errors.ExtensionNotFound:
				await ctx.send(f"**{i}** was not found")
			except errors.ExtensionAlreadyLoaded:
				await ctx.send(f"**{i}** is already loaded")

	@cog.command()
	async def unload(self, ctx, *cogs):
		for i in cogs:
			try:
				self.bot.unload_extension(f"cogs.{i}")
				await ctx.send(f"Unloaded **{i}**")
			except errors.ExtensionNotLoaded:
				pass

	@command()
	async def reload(self, ctx, *cogs):
		for i in cogs:
			self.bot.reload_extension(i)
			await ctx.send(f"Reloaded **{i}**")

	####################################### CLEAR
	@command(aliases=["purge", "prune"])
	@has_permissions(manage_messages=True)
	async def clear(self, ctx, amount: int):
		await ctx.channel.purge(limit=amount + 1)

	@clear.error
	async def bad_usage(self, ctx, error):
		if isinstance(error, (errors.BadArgument, errors.MissingRequiredArgument, errors.CommandInvokeError)):
			await ctx.message.delete()
		else:
			raise error

	#######################################
	@command()
	@staticmethod
	async def avatar(ctx, target: FindMember):
		await ctx.send(target.avatar_url if isinstance(target, discord.Member) else f"User **{target}** not found")


def setup(client):
	client.add_cog(Commands(client))