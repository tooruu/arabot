from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import *
#import discord


class Listeners(Cog):
	def __init__(self, client):
		self.bot = client

		#await startTimer()

	"""
	from datetime import datetime, timedelta

	async def startTimer(self):
		now = datetime.now
		resets = [0, 3, 5, 7]
		while True:
			# Find next event reset date
			async for i in arange(len(resets)):
				today = now()
				if resets[i] <= today.weekday() < resets[i + 1]:
					reset = (today + timedelta(days=resets[i + 1] - today.weekday()
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
				await bot.get_channel(678423053306298389).edit(name=f"🌍 {hours}h {minutes}m")
"""

	@Cog.listener()
	@staticmethod
	async def on_command_error(ctx, error):
		if hasattr(ctx.command, "on_error"):
			return
		if isinstance(error, commands.CommandNotFound):
			return
		if isinstance(error, (commands.errors.MissingPermissions, commands.errors.CheckFailure)):
			print(f"Missing permissions: {ctx.author}: {ctx.message.content[1:]}")
			await ctx.send(f"Missing permissions: {ctx.author}: {ctx.message.content[1:]}")
			return
		raise error


def setup(client):
	client.add_cog(Listeners(client))