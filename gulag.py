import os
from datetime import datetime, timedelta
import time
import discord

client = discord.Client()


@client.event
async def on_ready():
	now = datetime.now

	resets = [0, 3, 5, 7]

	while True:

		# Find next event reset date
		for i in range(len(resets)):
			today = now()
			if resets[i] <= today.weekday() < resets[i + 1]:
				reset = (today +
					timedelta(days=resets[i + 1] - today.weekday()
					)).replace(hour=0, minute=0, second=0, microsecond=0)
				break

		# Count down
		while True:
			time.sleep(20)
			totalSeconds = (reset - now()).total_seconds()
			if totalSeconds <= 0:
				break
			hours = int(totalSeconds / 3600)
			minutes = int(totalSeconds % 3600 / 60) + 1
			await client.get_channel(678423053306298389).edit(
				name=f"OW: {hours}h {minutes}m"
			)


@client.event
async def on_message(msg):
	if msg.author == client.user:
		return
	if msg.content == "?":
		await msg.channel.send("!")
	elif msg.content == ";stop":
		await client.logout()
	elif msg.content.startswith(";rename"):
		msgParts = msg.content.split(" ")
		if len(msgParts) >= 3 and msgParts[1].isdigit():
			await client.get_channel(int(msgParts[1])
				).edit(name=" ".join(map(str, msgParts[2:])))

token = os.environ["token"]
client.run(token)