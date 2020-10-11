from glob import glob
from discord.ext.commands import (command, Cog, check, has_permissions, group, errors, MessageConverter, cooldown, BucketType, CommandOnCooldown)
from .._utils import (FindMember, isDev, FindChl, BOT_NAME, BOT_VERSION, setPresence, FindEmoji, bold)
import discord
from io import BytesIO

class Commands(Cog):
	def __init__(self, client):
		self.bot = client

	@command(aliases=["ver", "v"], brief="| Show currently running bot's version")
	async def version(self, ctx):
		await ctx.send(f"{BOT_NAME} v{BOT_VERSION}")

	@command(brief="<user> | Tell chat you love someone")
	async def love(self, ctx, partner: FindMember):
		await ctx.send(f"{ctx.author.mention} loves {partner.mention} :heart:" if partner else "Love partner not found")

	@command(aliases=["exit", "quit", "kill", "shine", "shineo", "die", "kys", "begone", "fuck"], hidden=True)
	@check(isDev)
	async def stop(self, ctx):
		await ctx.send("I'm dying, master :cold_face:")
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

	@group(aliases=["cogs"], invoke_without_command=True, hidden=True)
	@check(isDev)
	async def cog(self, ctx):
		await ctx.send("Loaded cogs: " + ", ".join(bold(c) for c in self.bot.cogs))

	@cog.command(aliases=["enable"])
	@check(isDev)
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

	@cog.command(aliases=["disable"])
	@check(isDev)
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
	@check(isDev)
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

	@command(aliases=["a", "pfp"], brief="<user> | Show full-sized version of user's avatar")
	async def avatar(self, ctx, target: FindMember = False):
		if target is None:
			await ctx.send("User not found")
		else:
			if target is False:
				target = ctx.author
			await ctx.send(
				embed=discord.Embed().set_image(url=str(target.avatar_url_as(static_format="png"))
															).set_footer(text=(target.display_name) + "'s avatar")
			)

	@command(aliases=["r"], brief="<emoji> | Show your big reaction to everyone")
	async def react(self, ctx, emoji: FindEmoji):
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
		files = {str(emoji.url) if isinstance(emoji, (discord.Emoji, discord.PartialEmoji)) else emoji for emoji in emojis if emoji is not None}
		#discord.File(BytesIO(await emoji.url.read()),
		#str(emoji.url).split("/")[-1].partition("?")[0])
		#files.append(discord.File(BytesIO(await img.read()), emoji.split("/")[-1]))
		await ctx.send("\n".join(files) if files else "No emojis found")

	@command(brief="<user> | DM user to summon them")
	async def summon(self, ctx, target: FindMember):
		if target:
			invite = discord.Embed.Empty
			for invite in await ctx.guild.invites():
				if invite.max_uses == 0:
					invite = invite.url
					break
			await target.send(
				embed=discord.Embed(description=f"{ctx.author.mention} is summoning you to {ctx.channel.mention}").set_author(name=ctx.guild.name, url=invite, icon_url=str(ctx.guild.icon_url_as(static_format="png")) or discord.Embed.Empty)
			)
			await ctx.send(f"Summoning {target.mention}")
		else:
			await ctx.send("User not found")

	@command(brief="| Get a random inspirational quote")
	async def inspire(self, ctx):
		async with self.bot.ses.get("https://inspirobot.me/api?generate=true") as url:
			#async with self.bot.ses.get(url := await url.text()) as img:
			#	await ctx.send(file=discord.File(BytesIO(await img.read()), url.split("/")[-1]))
			await ctx.send(await url.text())

	@command(hidden=True)
	@has_permissions(manage_messages=True)
	async def say(self, ctx, *, msg):
		await ctx.message.delete()
		await ctx.send(msg)

	@cooldown(1, 10, BucketType.channel)
	@command(brief="Who asked?", hidden=True)
	async def wa(self, ctx, msg: MessageConverter = None):
		await ctx.message.delete()
		if msg:
			for i in "🇼", "🇭", "🇴", "🇦", "🇸", "🇰", "🇪", "🇩", "<:FukaWhy:677955897200476180>":
				await msg.add_reaction(i)
			return
		async for msg in ctx.history(limit=3):
			if not msg.author.bot:
				for i in "🇼", "🇭", "🇴", "🇦", "🇸", "🇰", "🇪", "🇩", "<:FukaWhy:677955897200476180>":
					await msg.add_reaction(i)
				break

	@wa.error
	async def wa_ratelimit(self, ctx, error):
		if isinstance(error, CommandOnCooldown):
			await ctx.message.delete()
			return
		raise error

	@command(hidden=True)
	async def lines(self, ctx):
		count = 0
		for g in glob("./bot/**/[!_]*.py", recursive=True) + ["./bot/cogs/_utils.py"]:
			with open(g, encoding="utf8") as f:
				count += len(f.readlines())
		await ctx.send(f"{BOT_NAME} consists of **{count}** lines of code")


def setup(client):
	client.add_cog(Commands(client))