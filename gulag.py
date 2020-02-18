from datetime import datetime, timedelta
from http.client import HTTPException
from asyncio import sleep
import discord
from discord.ext.commands import Bot

client = Bot(command_prefix=";")


async def setPresence(_type, name, status=None):
	await client.change_presence(
		status=status or discord.Status.dnd,
		activity=discord.Activity(name, type = _type )
	)


async def startTimer():
	now = datetime.now

	resets = [0, 3, 5, 7]

	async def arange(it):
		for v in range(it):
			yield v

	while True:

		# Find next event reset date
		async for i in arange(len(resets)):
			today = now() #- timedelta(hours=5)
			if resets[i] <= today.weekday() < resets[i + 1]:
				reset = (today +
					timedelta(days=resets[i + 1] - today.weekday()
					)).replace(hour=0, minute=0, second=0, microsecond=0)
				break

		# Count down
		while True:
			await asyncio.sleep(60)
			totalSeconds = (reset - now()).total_seconds()
			if totalSeconds <= 0:
				break
			hours = int(totalSeconds / 3600)
			minutes = int(totalSeconds % 3600 / 60) + 1
			await client.get_channel(678423053306298389).edit(
				name=f"OW: {hours}h {minutes}m"
			)


@client.event
async def on_ready():
	await setPresence(discord.ActivityType.watching, "#lewd")
	client.load_extension("cogs.lerolero")
	print("Ready!")
	await startTimer()


@client.command()
async def stop(ctx):
	await ctx.send("Stopping!")
	print("Stopping!")
	await client.logout()


@client.command()
async def rename(ctx, chanId, *, name):
	if chanId.isdigit():
		channel = client.get_channel(int(chanId))
		if channel is not None:
			oldName = channel.name
			try:
				await channel.edit(name=name)
				await ctx.send(f"Renamed **{oldName}** to **{channel.name}**")
			except HTTPException:
				await ctx.send(f"Failed renaming **{oldName}** to **{name}**")


@client.command()
async def status(ctx, _type, name):
	  if not int(_type) in [0,1,2,3]:
        return
    await setPresence(int(_type), name)


@client.command()
async def ping(ctx):
	await ctx.send(":ping_pong: Pong!")


@client.command(alises=["cogs"])
async def cog(ctx, mode, *, cogs):
	cogs = cogs.split(" ")
	if mode == "load":
		for i in cogs:
			client.load_extension(f"cogs.{i}")
	elif mode == "unload":
		for i in cogs:
			client.unload_extension(f"cogs.{i}")
	elif mode == "reload":
		for i in cogs:
			client.unload_extension(f"cogs.{i}")
			client.load_extension(f"cogs.{i}")


if __name__ == "__main__":
	try:
		import os
		token = os.environ["token"]
	except KeyError:
		with open("secret") as s:
			token = s.read()
	client.run(token)