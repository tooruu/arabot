from datetime import datetime, timedelta
from discord.ext.commands import Cog
from discord.ext.tasks import loop
now = datetime.now


class Timer(Cog):
	def __init__(self, client):
		self.bot = client
		self.reset = self.resetTime()
		self.countdown.start()

	resets = [0, 3, 5, 7]

	def resetTime(self):
		today = now()
		for i in range(len(self.resets)):
			if self.resets[i] <= today.weekday() < self.resets[i + 1]:
				return (today + timedelta(days=self.resets[i + 1] - today.weekday()
					)).replace(hour=0, minute=0, second=0, microsecond=0)

	@loop(minutes=1)
	async def countdown(self):
		totalSeconds = (self.reset - now()).total_seconds()
		if totalSeconds <= 0:
			totalSeconds = (self.resetTime() - now()).total_seconds()
		hours = int(totalSeconds / 3600)
		minutes = int(totalSeconds % 3600 / 60) + 1
		await self.channel.edit(name=f"🌍 {hours}h {minutes}m")

	@countdown.before_loop
	async def wait(self):
		await self.bot.wait_until_ready()
		self.channel = self.bot.get_channel(678423053306298389)

	def cog_unload(self):
		self.countdown.cancel()


def setup(client):
	client.add_cog(Timer(client))