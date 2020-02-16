from datetime import datetime, timedelta
import asyncio
from discord.ext import commands

client = commands.Bot(command_prefix=";")


@client.event
async def on_ready():
	print("Ready!")
	now = datetime.now

	resets = [0, 3, 5, 7]

	async def arange(it):
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
			await asyncio.sleep(20)
			totalSeconds = (reset - now()).total_seconds()
			if totalSeconds <= 0:
				break
			hours = int(totalSeconds / 3600)
			minutes = int(totalSeconds % 3600 / 60) + 1
			await client.get_channel(678423053306298389).edit(
				name=f"OW: {hours}h {minutes}m"
			)


@client.command()
async def stop(ctx):
	await ctx.send("Stopping!")
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
			except:
				await ctx.send(f"Failed renaming **{oldName}** to **{name}**")


@client.command()
async def lerolero(ctx):
	await ctx.channel.send(
		""":b::b::b::b::b::b::b::b::b::b::b::b::b::b::b:
:b::b::b::b::b::b::b::b:<:CommuThink:676973669796544542>:b::b::b::b::b::b:
:b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b::b:
:b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b:
:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:"""
	)
	await ctx.channel.send(
		"""
:b::b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:
:b::b::b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:
:b::b::b::b:<:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b::b::b::b::b::b::b::b::b::b::b::b::b::b:"""
	)


#token = os.environ["token"]
client.run("Njc3OTgyNDA4OTEzNTg0MTMw.XkcNhQ.p92-2LRTHkI2lKTY0iLY6t1zn9k")