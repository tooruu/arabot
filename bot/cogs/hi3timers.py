from datetime import datetime, timedelta, time
from discord.ext.commands import Cog, group, has_permissions
from discord.ext.tasks import loop
from ._utils import FindChl
now = datetime.now

class Timer:
	def __init__(self, channel, schedule):
		schedule = {k:sorted(v) for k,v in sorted(schedule.items())}
		self.sch = schedule
		self.channel = channel

	def get_next_phase(self): # TODO: TZ-aware timestamps
		cur_time = now()
		cur_wkday = cur_time.weekday()
		today = cur_time.date()
		wkdays = list(self.sch.keys())
		times = list(self.sch.values())
		if cur_wkday in wkdays:
			for tup in self.sch[cur_wkday]:
				if cur_time.time() < tup[0]:
					return datetime.combine(today, tup[0])
		for w in wkdays:
			if cur_wkday < w:
				next_wkday_date = today + timedelta(days=w - cur_wkday)
				return datetime.combine(next_wkday_date, self.sch[w][0][0])

	def till_next_phase(self):
		totalSeconds = (self.get_next_phase() - now()).total_seconds()
		hours = int(totalSeconds / 3600)
		minutes = int(totalSeconds % 3600 / 60)
		return hours, minutes

	def get_status(self):
		next_phase = self.get_next_phase()
		for tup in self.sch[next_phase.weekday()]:
			if tup[0] == next_phase.time():
				return tup[1]

class HI3Timers(Cog):
	def __init__(self, client):
		self.bot = client
		self.timers = {}

	@loop(minutes=5)
	async def countdown(self):
		ow = self.timers["ow"]
		ma = self.timers["ma"]
		await ow.channel.edit(name="🌍{} {}h {}m".format(ow.get_status(), *ow.till_next_phase()))
		await ma.channel.edit(name="👹{} {}h {}m".format(ma.get_status(), *ma.till_next_phase()))

	@Cog.listener()
	async def on_ready(self):
		self.timers["ow"] = Timer(self.bot.get_channel(678423053306298389), {
			0: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
			3: [(time(hour=4), "Ongoing")],
			5: [(time(hour=4), "Ongoing")],
		})
		self.timers["ma"] = Timer(self.bot.get_channel(752382371596206141), {
			0: [(time(hour=4), "Ongoing")],
			1: [(time(hour=4), "Calculating")],
		})
		self.countdown.start()

	@group(invoke_without_command=True, hidden=True)
	#@has_permissions(manage_guild=True)
	async def timer(self, ctx):
		#status = "active, running" if (task := self.countdown.get_task()) and not task.done() else "stopped"
		#channel = f"**{self.timers[t].name}**" if self.channel else "Not set"
		await ctx.send("Timers: " + ", ".join(self.timers))

	@timer.command()
	async def next(self, ctx, t):
		await ctx.send(self.timers[t].get_next_phase().strftime("%Y.%m.%d, %H:%M:%S") if self.timers.get(t) else f"Timer {t} not found")

	def cog_unload(self):
		self.countdown.cancel()

def setup(client):
	client.add_cog(HI3Timers(client))