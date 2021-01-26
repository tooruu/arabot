from datetime import datetime, timedelta, time
from discord.ext.commands import Cog, group
from discord.ext.tasks import loop


class Timer:
    def __init__(self, channel, schedule):
        schedule = {k: sorted(v) for k, v in sorted(schedule.items())}
        self.sch = schedule
        self.channel = channel

    def get_next_phase(self):  # TODO: TZ-aware timestamps
        cur_time = datetime.now()
        cur_wkday = cur_time.isoweekday()
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
        firstWkday_date = today + timedelta(days=(wkdays[0] - cur_wkday) % 7)
        return datetime.combine(firstWkday_date, times[0][0][0])

    def till_next_phase(self):
        totalSeconds = (self.get_next_phase() - datetime.now()).total_seconds()
        hours = int(totalSeconds / 3600)
        minutes = int(totalSeconds % 3600 / 60)
        return hours, minutes

    def get_status(self):
        next_phase = self.get_next_phase()
        for tup in self.sch[next_phase.isoweekday()]:
            if tup[0] == next_phase.time():
                return tup[1]


class HI3Timers(Cog):
    def __init__(self, client):
        self.bot = client
        self.timers = {}

    @loop(minutes=5)  # rate limit: 2 updates per 10 mins
    async def countdown(self):
        ow = self.timers["ow"]
        ma = self.timers["ma"]
        qs = self.timers["qs"]
        waifus = self.timers["waifus"]
        await ow.channel.edit(name="🌍{} {}h {}m".format(ow.get_status(), *ow.till_next_phase()))
        await ma.channel.edit(name="👹{} {}h {}m".format(ma.get_status(), *ma.till_next_phase()))
        await qs.channel.edit(name="🔥{} {}h {}m".format(qs.get_status(), *qs.till_next_phase()))
        await waifus.channel.edit(name="💖Waifus in {}m".format(waifus.till_next_phase()[1]))

    @Cog.listener()
    async def on_ready(self):
        self.timers["ow"] = Timer(
            self.bot.get_channel(678423053306298389),
            {
                1: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
                4: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
                6: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
            },
        )
        self.timers["ma"] = Timer(
            self.bot.get_channel(779022842372685854),
            {
                1: [(time(hour=4), "Ongoing")],
                2: [(time(hour=4), "Calculating")],
            },
        )
        self.timers["qs"] = Timer(
            self.bot.get_channel(752382371596206141),
            {
                1: [(time(hour=15), "Preparing")],
                3: [
                    (time(hour=22), "Ongoing"),
                    (time(hour=22, minute=30), "Finalizing"),
                ],
                5: [(time(hour=15), "Preparing")],
                7: [
                    (time(hour=22), "Ongoing"),
                    (time(hour=22, minute=30), "Finalizing"),
                ],
            },
        )
        self.timers["waifus"] = Timer(
            self.bot.get_channel(779019769755861004),
            {w: [(time(hour=h, minute=39), None) for h in range(23)] for w in range(1, 8)},
        )
        self.countdown.start()

    @group(invoke_without_command=True, hidden=True)
    # @has_permissions(manage_guild=True)
    async def timer(self, ctx):
        # status = "active, running" if (task := self.countdown.get_task()) and not task.done() else "stopped"
        # channel = f"**{self.timers[t].name}**" if self.channel else "Not set"
        await ctx.send("Timers: " + ", ".join(self.timers))

    @timer.command()
    async def next(self, ctx, t):
        await ctx.send(
            f"Next phase is on {self.timers[t].get_next_phase().strftime('%A, %H:%M')} server time"
            if self.timers.get(t)
            else f"Timer **{t}** not found"
        )

    def cog_unload(self):
        self.countdown.cancel()


def setup(client):
    client.add_cog(HI3Timers(client))
