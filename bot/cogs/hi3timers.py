from datetime import datetime, timedelta, time
from discord.ext.commands import Cog, group, has_permissions
from discord.ext.tasks import loop
from ._utils import FindChl
now = datetime.now

class Timer:
	def __init__(self, channel, schedule):
		self.sch = schedule
		self.next_phase = self.get_next_phase()
		self.channel = channel

	def get_next_phase(self): # assumes time is 0, needs fix
		today = now()
		wkdays = list(self.sch.keys())
		for i in range(len(wkdays)):
			if wkdays[i] <= today.weekday() < wkdays[i + 1]:
				return datetime.combine(today + timedelta(days=wkdays[i + 1] - today.weekday()), list(self.sch.values())[i + 1][0])

	def till_next(self):
		totalSeconds = (self.next_phase - now()).total_seconds()
		if totalSeconds <= 0:
			totalSeconds = (self.get_next_phase() - now()).total_seconds()
		hours = int(totalSeconds / 3600)
		minutes = int(totalSeconds % 3600 / 60) + 1
		return hours, minutes

	def get_phase(self):
		today = now()
		wkdays = list(self.sch.keys())
		for i in range(len(wkdays)):
			if wkdays[i] <= today.weekday() < wkdays[i + 1]:
				return list(self.sch.values())[i][1]

class HI3Timers(Cog):
	def __init__(self, client):
		self.bot = client
		self.timers = {}

	@loop(minutes=1)
	async def countdown(self):
		ow = self.timers["ow"]
		await ow.channel.edit(name="🌍{} {}h {}m".format(ow.get_phase(), *ow.till_next()))

	@Cog.listener()
	async def on_ready(self):
		self.timers["ow"] = Timer(self.bot.get_channel(678423053306298389), {0:(time(hour=4), "Ongoing"),3:(time(hour=4), "Ongoing"),5:(time(hour=4), "Ongoing"),7:(time(hour=4), "Ongoing")})
		self.countdown.start()

	@group(invoke_without_command=True, hidden=True)
	@has_permissions(manage_guild=True)
	async def timer(self, ctx):
		status = "active, running" if (task := self.countdown.get_task()) and not task.done() else "stopped"
		#channel = f"**{self.timers[t].name}**" if self.channel else "Not set"
		await ctx.send("Status: " + status)

	@timer.command(name="set")
	async def set_channel(self, ctx, t, chan: FindChl):
		if chan:
			self.timers[t].channel = chan
			await ctx.send(f"Channel set to **{chan.name}**")
		else:
			await ctx.send("Channel not found")

	@timer.command()
	async def start(self, ctx):
		self.countdown.start()
		await ctx.send("Started timer")

	@timer.command()
	async def stop(self, ctx):
		self.countdown.cancel() # cancel() != stop()
		await ctx.send("Stopping timer")

	def cog_unload(self):
		self.countdown.cancel()

def setup(client):
	client.add_cog(HI3Timers(client))