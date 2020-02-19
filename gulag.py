from datetime import datetime, timedelta
from asyncio import sleep
import discord
from discord.ext import commands

client = commands.Bot(command_prefix=";")

isDev = lambda ctx: ctx.author.id in (337343326095409152, 447138372121788417)


async def setPresence(_type: int, name: str, _status=None):
	if isinstance(_status, discord.Status):
		await client.change_presence(
			status=_status, activity=discord.Activity(name=name, type=_type)
		)
		return
	await client.change_presence(activity=discord.Activity(name=name, type=_type))


async def startTimer():
	now = datetime.now

	resets = [0, 3, 5, 7]

	async def arange(it: int):
		for v in range(it):
			yield v

	while True:

		# Find next event reset date
		async for i in arange(len(resets)):
			today = now()
			if resets[i] <= today.weekday() < resets[i + 1]:
				reset = (today +
					timedelta(days=resets[i + 1] - today.weekday()
					)).replace(hour=0, minute=0, second=0, microsecond=0)
				break

		# Count down
		while True:
			await sleep(60)
			totalSeconds = (reset - now()).total_seconds()
			if totalSeconds <= 0:
				break
			hours = int(totalSeconds / 3600)
			minutes = int(totalSeconds % 3600 / 60) + 1
			await client.get_channel(678423053306298389).edit(
				name=f"🌍 Ongoing {hours}h {minutes}m"
			)


@client.event
async def on_ready():
	await setPresence(discord.ActivityType.watching, "#lewd")
	client.load_extension("cogs.communism")
	print("Ready!")
	await startTimer()


@client.command()
@commands.check(isDev)
async def stop(ctx):
	await ctx.send("Stopping!")
	print("Stopping!")
	await client.logout()


@client.command()
@commands.has_permissions(manage_guild=True)
async def rename(ctx, chan: discord.TextChannel, *, name):
	oldName = chan.name
	await chan.edit(name=name)
	await ctx.send(f"Renamed **{oldName}** to **{chan.name}**")


@client.command()
@commands.check(isDev)
async def status(ctx, _type: int, *, name):
	if _type not in (0, 1, 2, 3):
		return
	await setPresence(_type, name)


@client.command(name="177013")
async def _177013(ctx):
	await setPresence(3, "177013 with yo mama")


@client.command()
async def ping(ctx):
	await ctx.send(f":ping_pong: Pong after {round(client.latency, 3)}ms!")


@client.group(aliases=["cogs"])
@commands.check(isDev)
async def cog(ctx):
	pass


@cog.command()
async def load(ctx, *cogs):
	for i in cogs:
		try:
			client.load_extension(f"cogs.{i}")
			await ctx.send(f"Loaded **{i}**")
		except commands.errors.ExtensionNotFound:
			await ctx.send(f"**{i}** was not found")
		except commands.errors.ExtensionAlreadyLoaded:
			await ctx.send(f"**{i}** is already loaded")


@cog.command()
async def unload(ctx, *cogs):
	for i in cogs:
		try:
			client.unload_extension(f"cogs.{i}")
			await ctx.send(f"Unloaded **{i}**")
		except commands.errors.ExtensionNotLoaded:
			pass


@cog.command()
async def reload(ctx, *cogs):
	await unload(ctx, *cogs)
	await load(ctx, *cogs)


@client.command(aliases=["purge", "prune"])
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
	await ctx.channel.purge(limit=amount + 1)


@clear.error
async def bad_usage(ctx, error):
	if isinstance(
		error, (
		commands.errors.BadArgument, commands.errors.MissingRequiredArgument,
		commands.errors.CommandInvokeError
		)
	):
		await ctx.message.delete()
		return
	raise error


@client.event
async def on_command_error(ctx, error):
	if hasattr(ctx.command, "on_error"):
		return
	if isinstance(error, commands.CommandNotFound):
		return
	if isinstance(
		error, (commands.errors.MissingPermissions, commands.errors.CheckFailure)
	):
		await ctx.send(f"Missing permissions: {ctx.author}: {ctx.message.content[1:]}")
		print(f"Missing permissions: {ctx.author}: {ctx.message.content[1:]}")
		return
	raise error


if __name__ == "__main__":
	try:
		import os
		token = os.environ["token"]
	except KeyError:
		with open("secret") as s:
			token = s.read()
	client.run(token)