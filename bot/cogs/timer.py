from datetime import datetime, timedelta
from discord.ext.commands import Cog, group, has_permissions
from discord.ext.tasks import loop
from ._utils import FindChl
now = datetime.now


#pylint: disable=attribute-defined-outside-init
class Timer(Cog):
	def __init__(self, client):
		self.bot = client
		self.resets = 0, 3, 5, 7
		self.channel = None

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
	async def set_reset_time(self):
		self.reset = self.resetTime()

	@Cog.listener()
	async def on_ready(self):
		self.channel = self.bot.get_channel(678423053306298389)
		self.countdown.start()

	@group(invoke_without_command=True)
	@has_permissions(manage_guild=True)
	async def timer(self, ctx):
		#pylint: disable=used-before-assignment
		status = "Active, running" if (task:=self.countdown.get_task()) and not task.done() else "Stopped"
		channel = f"**{self.channel.name}**" if self.channel else "Not set"
		await ctx.send(f"Channel: {channel}\nStatus: {status}")

	@timer.command(name="set")
	async def set_(self, ctx, chan: FindChl):
		if chan:
			self.channel = chan
			await ctx.send(f"Channel set to **{chan.name}**")
		else:
			await ctx.send("Channel not found")

	@timer.command()
	async def start(self, ctx):
		if self.channel:
			self.countdown.start()
			await ctx.send("Started timer")
		else:
			await ctx.send("Channel not set!")

	@timer.command(aliases=["stop"]) # stop() != cancel()
	async def cancel(self, ctx):
		self.countdown.cancel()
		await ctx.send("Stopping timer")

	def cog_unload(self):
		self.countdown.cancel()


def setup(client):
	client.add_cog(Timer(client))