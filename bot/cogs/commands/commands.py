from discord.ext.commands import command, Cog, check, has_permissions, group, errors
from .._utils import (
	FindMember, isDev, FindChl, BOT_NAME, BOT_VERSION, setPresence, FindEmoji, MemberConverter, getenv, bold, dsafe
)
import discord
from aiohttp import ClientSession as WebSession, ContentTypeError
from jikanpy import AioJikan
from urllib.parse import quote_plus as safe, quote
from io import BytesIO
from json import loads

class Commands(Cog):
	def __init__(self, client):
		self.bot = client
		(self.token, self.g_search_key, self.g_isearch_key, self.g_cse, self.g_yt_key, self.faceit_key, self.wolfram_id
			) = getenv("token", "g_search_key", "g_isearch_key", "g_cse", "g_yt_key", "faceit_key", "wolfram_id")

	@command(aliases=["ver", "v"], brief="| Show currently running bot's version")
	async def version(self, ctx):
		await ctx.send(f"{BOT_NAME} v{BOT_VERSION}")

	@command()
	async def ping(self, ctx):
		await ctx.send(f":ping_pong: Pong after {self.bot.latency*1000:.0f}ms!")

	@command(brief="<user> | Make everyone know you love someone")
	async def love(self, ctx, partner: FindMember):
		await ctx.send(f"{ctx.author.mention} loves {partner.mention} :heart:" if partner else "Love partner not found")

	@command(aliases=["exit", "quit", "kill", "shine", "shineo", "die", "kys"], hidden=True)
	@check(isDev)
	async def stop(self, ctx):
		await ctx.send("Oh no! I'm dying... :cold_face:")
		print("Stopping!")
		await self.bot.close()

	@command(aliases=["cren"], hidden=True)
	@has_permissions(manage_guild=True)
	async def crename(self, ctx, chan: FindChl, *, name):
		oldName = chan.name
		await chan.edit(name=name)
		await ctx.send(f"Renamed {bold(oldName)} to {bold(chan.name)}")

	@command(hidden=True)
	@check(isDev)
	async def status(self, ctx, _type: int, *, name):
		if _type not in (0, 1, 2, 3):
			return
		await setPresence(self.bot, _type, name)

	@command(name="177013")
	async def _177013(self, ctx):
		await setPresence(self.bot, 3, "177013 with yo mama")

	@command(aliases=["source"], brief="<link|attachment> | Find anime source for an image")
	async def sauce(self, ctx, image_url=None):
		if image_url := ctx.message.attachments[0].url if ctx.message.attachments else image_url if image_url.startswith(
			"http"
		) else None:
			async with ctx.typing():
				async with WebSession() as session:
					async with session.get("https://trace.moe/api/search?url=" + quote(image_url)) as tmoe_resp:
						try:
							mal_resp = (await AioJikan().anime((tmoe_resp := (await tmoe_resp.json())["docs"][0])["mal_id"]))
						except ContentTypeError:
							await ctx.send(
								"Unfortunately, the image was rejected by our sauce provider.\nHowever, you can still find the sauce manually at\nhttps://trace.moe/?url="
								+ safe(image_url)
							)
						else:
							async with session.get(
								"https://trace.moe/preview.php",
								params={
								"anilist_id": tmoe_resp["anilist_id"],
								"file": safe(tmoe_resp["filename"]),
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
									description=
									f"Similarity: {tmoe_resp['similarity']:.1%} | Score: {mal_resp['score']} | {mal_resp['status']}"
									).set_author(name=mal_resp["title"],
									url=mal_resp["url"]).set_thumbnail(url=mal_resp["image_url"]).add_field(
									name="Synopsis",
									value=s if len(s := mal_resp["synopsis"].partition(" [")[0]) <=
									(maxlength := 600) else ".".join(s[:maxlength].split(".")[0:-1]) + "..."
									).set_footer(
									text=f"Requested by {ctx.author.display_name} | Powered by trace.moe",
									icon_url=ctx.author.avatar_url
									)
								)

	@group(aliases=["cogs"], invoke_without_command=True, hidden=True)
	@check(isDev)
	async def cog(self, ctx):
		await ctx.send("Loaded cogs: " + ", ".join(bold(c) for c in self.bot.cogs))

	@cog.command(aliases=["add"])
	async def load(self, ctx, *cogs):
		loaded = []
		for i in cogs:
			try:
				self.bot.load_extension(f"cogs.{i}")
				loaded.append(bold(i))
			except errors.ExtensionNotFound:
				await ctx.send(bold(i) + " was not found")
			except errors.ExtensionAlreadyLoaded:
				await ctx.send(bold(i) + " is already loaded")
			except (errors.ExtensionFailed, errors.NoEntryPointError):
				await ctx.send(bold(i) + " is an invalid extension")
		await ctx.send("Loaded " + (", ".join(loaded) or "nothing"))

	@cog.command(aliases=["remove"])
	async def unload(self, ctx, *cogs):
		unloaded = []
		for i in cogs:
			try:
				self.bot.unload_extension(f"cogs.{i}")
				unloaded.append(bold(i))
			except errors.ExtensionNotLoaded:
				pass
		await ctx.send("Unloaded " + (", ".join(unloaded) or "nothing"))

	@cog.command()
	async def reload(self, ctx, *cogs):
		reloaded = []
		for i in cogs:
			try:
				self.bot.reload_extension(f"cogs.{i}")
				reloaded.append(bold(i))
			except errors.ExtensionNotFound:
				await ctx.send(bold(i) + " was not found")
			except errors.ExtensionNotLoaded:
				self.bot.load_extension(f"cogs.{i}")
				reloaded.append(bold(i))
			except (errors.ExtensionFailed, errors.NoEntryPointError):
				await ctx.send(bold(i) + " is an invalid extension")
		await ctx.send("Reloaded " + (", ".join(reloaded) or "nothing"))

	@command(aliases=["purge", "prune", "d"], hidden=True)
	@has_permissions(manage_messages=True)
	async def clear(self, ctx, amount: int = None):
		if amount:
			await ctx.channel.purge(limit=amount + 1)
		else:
			await ctx.message.delete()

	@command(aliases=["a"], brief="<user> | Show full-sized version of user's avatar")
	async def avatar(self, ctx, target: FindMember):
		if target:
			await ctx.send(
				embed=discord.Embed().set_image(url=str(target.avatar_url_as(static_format="png"))
															).set_footer(text=(target.display_name) + "'s avatar")
			)
		else:
			await ctx.send("User not found")

	@command(aliases=["r"], brief="<emoji> | Show your big reaction to everyone")
	async def reaction(self, ctx, emoji: FindEmoji):
		if emoji:
			await ctx.message.delete()
			await ctx.send(
				embed=discord.Embed().set_image(url=emoji.url).
				set_footer(text="reacted", icon_url=ctx.author.avatar_url_as(static_format="png"))
			)
		else:
			await ctx.send("Emoji not found")

	@command(aliases=["emote", "e"], brief="<emoji...> | Show full-sized versions of emoji(s)")
	async def emoji(self, ctx, *emojis: FindEmoji):
		files = []
		async with ctx.typing():
			async with WebSession() as session:
				for emoji in emojis:
					if isinstance(emoji, discord.Emoji):
						files.append(
							discord.File(BytesIO(await emoji.url.read()),
							str(emoji.url).split("/")[-1].partition("?")[0])
						)
					elif isinstance(emoji, str):
						async with session.get(emoji) as img:
							if img.status == 200:
								files.append(discord.File(BytesIO(await img.read()), emoji.split("/")[-1]))
			if files:
				if len(files) <= 10:
					await ctx.send(files=files)
				else:
					await ctx.send("Too many emojis passed, sending first 10", files=files[:10])
			else:
				await ctx.send("No emojis found")

	@command(brief="<user> | DM the user to make him come")
	async def call(self, ctx, target: MemberConverter): # Not use smart lookup
		if target:
			if target.dm_channel is None:
				await target.create_dm()
			await target.dm_channel.send(f"{ctx.author.display_name} wants you to show up in {bold(ctx.guild.name)}.")
			await ctx.send(f"Notified {target.mention}")
		else:
			await ctx.send("User not found")

	@command(brief="| Get a random inspirational quote")
	async def inspire(self, ctx):
		async with WebSession() as session:
			async with session.get("https://inspirobot.me/api", params={"generate": "true"}) as url:
				async with session.get(url := (await url.read()).decode()) as img:
					await ctx.send(file=discord.File(BytesIO(await img.read()), url.split("/")[-1]))

	@command(aliases=["i", "img"], brief="<query> | Top 3 search results from Google Images")
	async def image(self, ctx, *, query):
		async with WebSession() as session:
			async with session.get(
				"https://www.googleapis.com/customsearch/v1",
				params={
				"key": self.g_isearch_key,
				"cx": self.g_cse,
				"q": safe(query),
				"num": 1,
				"searchType": "image"
				}
			) as response:
				try:
					await ctx.send((await response.json())["items"][0]["link"])
				except KeyError:
					await ctx.send("No images found")

	@command(aliases=["g"], brief="<query> | Top 3 search results from Google")
	async def google(self, ctx, *, query):
		async with WebSession() as session:
			async with session.get(
				"https://www.googleapis.com/customsearch/v1",
				params={
				"key": self.g_search_key,
				"cx": self.g_cse,
				"q": safe(query),
				"num": 3
				}
			) as response:
				embed = discord.Embed(
					title="Google search results",
					description="Showing top 3 search results",
					url="https://google.com/search?q=" + safe(query)
				)
				try:
					for result in (await response.json())["items"]:
						embed.add_field(
							name=result["link"], value=f"{bold(result['title'])}\n{result['snippet']}", inline=False
						)
				except KeyError:
					await ctx.send("No results found")
				else:
					await ctx.send(embed=embed)

	@command(aliases=["yt3"], brief="<query> | Top 3 search results from YouTube")
	async def youtube3(self, ctx, *, query): #TODO: Use YouTube API
		async with WebSession() as session:
			async with session.get(
				"https://www.googleapis.com/customsearch/v1",
				params={
				"key": self.g_search_key,
				"cx": self.g_cse,
				"q": safe(query + " site:youtube.com/watch"),
				"num": 3
				}
			) as response:
				embed = discord.Embed(
					title="YouTube search results",
					description="Showing top 3 search results",
					url="https://google.com/search?q=" + safe(query + "+site:youtube.com/watch", safe="+")
				)
				try:
					for result in (await response.json())["items"]:
						embed.add_field(
							name=result["link"], value=f"{bold(result['title'])}\n{result['snippet']}", inline=False
						)
				except KeyError:
					await ctx.send("No videos found")
				else:
					await ctx.send(embed=embed)

	@command(aliases=["yt"], brief="<query> | Top search result from YouTube")
	async def youtube(self, ctx, *, query): #TODO: Use YouTube API
		async with WebSession() as session:
			async with session.get(
				"https://www.googleapis.com/customsearch/v1",
				params={
				"key": self.g_search_key,
				"cx": self.g_cse,
				"q": safe(query + " site:youtube.com/watch"),
				"num": 1
				}
			) as response:
				try:
					await ctx.send((await response.json())["items"][0]["link"])
				except KeyError:
					await ctx.send("No videos found")

	@command(brief="<nickname> | View player's FACEIT profile")
	async def faceit(self, ctx, nickname):
		async with WebSession(headers={"Authorization": "Bearer " + self.faceit_key}) as session:
			async with session.get(
				f"https://open.faceit.com/data/v4/search/players?nickname={nickname}&limit=1"
			) as player_search:
				if not (await player_search.json())["items"]:
					await ctx.send("Player not found")
					return
				async with session.get(
					"https://open.faceit.com/data/v4/players/" + (await player_search.json())["items"][0]["player_id"]
				) as player:
					player = await player.json()
		embed = discord.Embed(
			color=0xFF5500,
			description=
			f"[Steam profile](https://www.steamcommunity.com/profiles/{player['steam_id_64']})\nCountry: {player['country'].upper()} | Friends: {len(player['friends_ids'])} | Bans: {len(player['bans'])}\nFACEIT membership type: {player['membership_type']}"
		).set_author(name=player["nickname"],
			url=player["faceit_url"].format(lang="en")).set_thumbnail(url=player["avatar"])
		for game in player["games"]:
			embed.add_field(
				name=game.replace("_", " ").upper(),
				value=f"""Player name: {player['games'][game]['game_player_name']}
			Region: {player['games'][game]['region']}
			Skill level: {player['games'][game]['skill_level']}
			ELO: {player['games'][game]['faceit_elo']}""",
				inline=True
			)
		await ctx.send(embed=embed)

	@command(brief="<term> | Search term in Urban Dictionary", aliases=["ud"])
	async def urban(self, ctx, *, term):
		async with WebSession() as session:
			async with session.get(f"https://api.urbandictionary.com/v0/define?term={safe(term)}") as ud:
				ud = await ud.json()
		if ud := ud.get("list"):
			await ctx.send(
				embed=discord.Embed(
				description="\n---------------------------------\n".
				join([result["definition"].replace("[", "").replace("]", "") for result in ud[:3]])
				).set_author(name=term, url="https://www.urbandictionary.com/define.php?term=" + safe(term))
			)
		else:
			await ctx.send(f"Definition for {bold(term)} not found")

	@command(hidden=True)
	@has_permissions(manage_guild=True)
	async def say(self, ctx, *, msg):
		await ctx.message.delete()
		await ctx.send(msg)

	@command(brief="<query> | Answer a question?")
	async def calc(self, ctx, *, query):
		query = query.strip('`')
		async with ctx.typing():
			async with WebSession() as session:
				async with session.get(
					"https://api.wolframalpha.com/v2/query",
					params={
					"input": quote(query, safe=""),
					"format": "plaintext",
					"output": "json",
					"appid": self.wolfram_id,
					"units": "metric"
					}
				) as wa:
					wa = loads(await wa.text())["queryresult"]
			embed = discord.Embed(
				color=0xf4684c, title=dsafe(query), url="https://www.wolframalpha.com/input/?i=" + quote(query, safe="")
			).set_footer(
				icon_url="https://cdn.iconscout.com/icon/free/png-512/wolfram-alpha-2-569293.png", text="Wolfram|Alpha"
			)
			if wa["success"]:
				if wa.get("warnings"):
					embed.description = wa["warnings"]["text"]
				for pod in wa["pods"]:
					if pod["id"] == "Input":
						embed.add_field(
							name="Input",
							value=
							f"[{dsafe(pod['subpods'][0]['plaintext'])}](https://www.wolframalpha.com/input/?i={quote(pod['subpods'][0]['plaintext'], safe='')})"
						)
					if pod.get("primary"):
						embed.add_field(
							name="Result",
							value="\n".join(dsafe(subpod["plaintext"]) for subpod in pod["subpods"]),
							inline=False
						)
						break
			else:
				if wa.get("tips"):
					embed.description = wa["tips"]["text"]
			await ctx.send(embed=embed)

def setup(client):
	client.add_cog(Commands(client))