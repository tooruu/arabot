from glob import glob
from discord.ext.commands import (
	command, Cog, check, has_permissions, MessageConverter, cooldown, BucketType, CommandOnCooldown
)
from .._utils import FindMember, is_dev, BOT_NAME, set_presence, FindEmoji, bold
import discord

class General(Cog, name="Commands"):
	def __init__(self, client):
		self.bot = client

	@command(brief="<user> | Tell chat you love someone")
	async def love(self, ctx, partner: FindMember):
		await ctx.send(f"{ctx.author.mention} loves {partner.mention} :heart:" if partner else "Love partner not found")

	@command(aliases=["exit", "quit", "kill", "shine", "shineo", "die", "kys", "begone", "fuck"], hidden=True)
	@check(is_dev)
	async def stop(self, ctx):
		await ctx.send("I'm dying, master :cold_face:")
		print("Stopping!")
		await self.bot.close()

	@command(hidden=True)
	@check(is_dev)
	async def status(self, ctx, _type: int, *, name):
		if _type not in (0, 1, 2, 3):
			return
		await set_presence(self.bot, _type, name)

	@command(name="177013")
	async def _177013(self, ctx):
		await set_presence(self.bot, 3, "177013 with yo mama")

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
		files = {
			str(emoji.url) if isinstance(emoji, (discord.Emoji, discord.PartialEmoji)) else emoji
			for emoji in emojis if emoji is not None
		}
		#discord.File(BytesIO(await emoji.url.read()),
		#str(emoji.url).split("/")[-1].partition("?")[0])
		#files.append(discord.File(BytesIO(await img.read()), emoji.split("/")[-1]))
		await ctx.send("\n".join(files) if files else "No emojis found")

	@command(brief="<user> | DM user to summon them")
	async def summon(self, ctx, target: FindMember, *, msg=None):
		if target:
			invite = discord.Embed.Empty
			for i in await ctx.guild.invites():
				if i.max_uses == 0:
					invite = i.url
					break
			embed = discord.Embed(
				description=f"{ctx.author.mention} is summoning you to {ctx.channel.mention}" +
				(f"\n\n{bold(msg)}\n[Jump to message]({ctx.message.jump_url})" if msg else "")
			).set_author(
				name=ctx.guild.name,
				url=invite,
				icon_url=str(ctx.guild.icon_url_as(static_format="png")) or discord.Embed.Empty
			)
			try:
				await target.send(embed=embed)
				await ctx.send(f"Summoning {target.mention}")
			except:
				await ctx.send("An error occurred")
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
	client.add_cog(General(client))