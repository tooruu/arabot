from discord.ext.commands import command, Cog, check, has_permissions, group, errors
from .._utils import *
import discord
from aiohttp import ClientSession as WebSession, ContentTypeError
from jikanpy import AioJikan
from urllib.parse import quote
from io import BytesIO


class Commands(Cog):
	def __init__(self, client):
		self.bot = client
		(
			self.token,
			self.g_search_key,
			self.g_isearch_key,
			self.g_cse,
			self.g_yt_key,
		) = load_env("token", "g_search_key", "g_isearch_key", "g_cse", "g_yt_key")

	@command(aliases=["ver", "v"])
	async def version(self, ctx):
		await ctx.send(f"{BOT_NAME} v{BOT_VERSION}")

	@command()
	async def ping(self, ctx):
		await ctx.send(f":ping_pong: Pong after {self.bot.latency*1000:.0f}ms!")

	@command()
	async def love(self, ctx, partner: FindMember):
		await ctx.send(f"{ctx.author.mention} loves {partner.mention} :heart:" if partner else f"Love partner not found")

	@command(aliases=["exit", "quit"])
	@check(isDev)
	async def stop(self, ctx):
		await ctx.send("Stopping!")
		print("Stopping!")
		await self.bot.close()

	@command(aliases=["cren"])
	@has_permissions(manage_guild=True)
	async def crename(self, ctx, chan: FindChl, *, name):
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

	@command(aliases=["source"])
	async def sauce(self, ctx, image_url=None):
		if image_url:=ctx.message.attachments[0].url if ctx.message.attachments else image_url if image_url.startswith("http") else None:
			async with ctx.typing():
				async with WebSession() as session:
					async with session.get("https://trace.moe/api/search", params={"url": image_url}) as tmoe_resp:
						try:
							mal_resp = (await AioJikan(session=session).anime((tmoe_resp:=(await tmoe_resp.json())["docs"][0])["mal_id"]))
						except ContentTypeError:
							await ctx.send("Unfortunately, the image was rejected by our sauce provider.\nHowever, you can still find the sauce manually at\nhttps://trace.moe/?url=" + quote(image_url, safe=""))
						else:
							async with session.get(
								"https://trace.moe/preview.php",
								params={
								"anilist_id": tmoe_resp["anilist_id"],
								"file": quote(tmoe_resp["filename"]),
								"t": str(tmoe_resp["at"]),
								"token": tmoe_resp["tokenthumb"]
								}
							) as preview:
								#pylint: disable=used-before-assignment
								await ctx.send(
									f"*Episode {tmoe_resp['episode']} ({int(tmoe_resp['at']/60)}:{int(tmoe_resp['at']%60)})*",
									file=discord.File(BytesIO(await preview.read()), tmoe_resp["filename"]),
									embed=discord.Embed(
									color=32767,
									description=f"Similarity: {tmoe_resp['similarity']:.1%} | Score: {mal_resp['score']} | {mal_resp['status']}"
									).set_author(name=mal_resp["title"], url=mal_resp["url"]).set_thumbnail(url=mal_resp["image_url"]).add_field(
									name="Synopsis",
									value=s if len(s:=mal_resp["synopsis"].partition(" [")[0]) <= (maxlength:=600) else
									".".join(s[:maxlength].split(".")[0:-1]) + "..."
									).set_footer(
									text=f"Requested by {ctx.author.nick or ctx.author.name} | Powered by trace.moe",
									icon_url=ctx.author.avatar_url
									)
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
		if amount:
			await ctx.channel.purge(limit=amount + 1)
		else:
			await ctx.message.delete()

	@command(aliases=["a"])
	async def avatar(self, ctx, target: FindMember):
		if target:
			await ctx.send(embed=discord.Embed().set_image(url=str(target.avatar_url_as(static_format="png"))).set_footer(text=(target.nick or target.name) + "'s avatar"))
		else:
			await ctx.send("User not found")

	@command(aliases=["r"])
	async def reaction(self, ctx, emoji: FindEmoji):
		if emoji:
			await ctx.message.delete()
			await ctx.send(
				embed=discord.Embed().set_image(url=emoji.url).
				set_footer(text="reacted", icon_url=ctx.author.avatar_url_as(static_format="png"))
			)
		else:
			await ctx.send("Emoji not found")

	@command(aliases=["emote", "e"])
	async def emoji(self, ctx, *emojis: FindEmoji):
		files = []
		async with ctx.typing():
			async with WebSession() as session:
				for emoji in emojis:
					if isinstance(emoji, discord.Emoji):
						files.append(discord.File(
							BytesIO(await emoji.url.read()),
							str(emoji.url).split("/")[-1].partition("?")[0]
						))
					elif isinstance(emoji, str):
						async with session.get(emoji) as img:
							files.append(discord.File(BytesIO(await img.read()), emoji.split("/")[-1]))
			if files:
				if len(files) <= 10:
					await ctx.send(files=files)
				else:
					await ctx.send("Too many emojis passed, sending first 10", files=files[:10])
			else:
				await ctx.send("No emojis found")


	@command()
	async def call(self, ctx, target: MemberConverter): # Not use smart lookup
		if target:
			if target.dm_channel is None:
				await target.create_dm()
			await target.dm_channel.send(f"{ctx.author.name} wants you to show up in **{ctx.guild.name}**.")
			await ctx.send(f"Notified {target.mention}")
		else:
			await ctx.send("User not found")

	@command()
	async def inspire(self, ctx):
		async with WebSession() as session:
			async with session.get("https://inspirobot.me/api", params={"generate": "true"}) as url:
				async with session.get(url:=(await url.read()).decode()) as img:
					await ctx.send(file=discord.File(BytesIO(await img.read()), url.split("/")[-1]))

	@command(aliases=["i", "img"])
	async def image(self, ctx, *, query):
		async with WebSession() as session:
			async with session.get(
				"https://www.googleapis.com/customsearch/v1",
				params={
				"key": self.g_isearch_key,
				"cx": self.g_cse,
				"q": quote(query, safe=""),
				"num": 1,
				"searchType": "image"
				}
			) as response:
				try:
					await ctx.send((await response.json())["items"][0]["link"])
				except KeyError:
					await ctx.send("No images found")

	@command(aliases=["g"])
	async def google(self, ctx, *, query):
		async with WebSession() as session:
			async with session.get(
				"https://www.googleapis.com/customsearch/v1",
				params={
				"key": self.g_search_key,
				"cx": self.g_cse,
				"q": quote(query, safe=""),
				"num": 3
				}
			) as response:
				embed = discord.Embed(title="Google search results", description="Showing top 3 search results", url="https://google.com/search?q=" + quote(query))
				try:
					for result in (await response.json())["items"]:
						embed.add_field(name=result["link"], value=f"**{result['title']}**\n{result['snippet']}", inline=False)
				except KeyError:
					await ctx.send("No results found")
				else:
					await ctx.send(embed=embed)

	@command(aliases=["yt"])
	async def youtube(self, ctx, *, query): #TODO: Use YouTube API
		async with WebSession() as session:
			async with session.get(
				"https://www.googleapis.com/customsearch/v1",
				params={
				"key": self.g_search_key,
				"cx": self.g_cse,
				"q": quote(query + " site:youtube.com/watch", safe=""),
				"num": 3
				}
			) as response:
				embed = discord.Embed(title="YouTube search results", description="Showing top 3 search results", url="https://google.com/search?q=" + quote(query + "+site:youtube.com/watch", safe="+"))
				try:
					for result in (await response.json())["items"]:
						embed.add_field(name=result["link"], value=f"**{result['title']}**\n{result['snippet']}", inline=False)
				except KeyError:
					await ctx.send("No videos found")
				else:
					await ctx.send(embed=embed)


def setup(client):
	client.add_cog(Commands(client))