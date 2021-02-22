from datetime import datetime, timedelta, time
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from pytz import timezone, UTC


class Timer:
    def __init__(self, schedule, tz=UTC):  # tz - Pytz timezone object
        self.sched = {
            wkday: sorted(zip(map(tz.localize, (t[0] for t in times)), (t[1] for t in times)))
            for wkday, times in sorted(schedule.items())
        }
        self.tz = tz

    def get_next_phase(self):
        cur_time = datetime.now(tz=self.tz)
        cur_wkday = cur_time.isoweekday()
        today = cur_time.date()
        wkdays = list(self.sched.keys())
        times = list(self.sched.values())
        if cur_wkday in wkdays:
            for tup in self.sched[cur_wkday]:
                if cur_time.timetz() < tup[0]:
                    return datetime.combine(today, tup[0])
        for w in wkdays:
            if cur_wkday < w:
                next_wkday_date = today + timedelta(days=w - cur_wkday)
                return datetime.combine(next_wkday_date, self.sched[w][0][0])
        first_wkday_date = today + timedelta(days=(wkdays[0] - cur_wkday) % 7)
        return datetime.combine(first_wkday_date, times[0][0][0])

    def till_next_phase(self):
        totalSeconds = (self.get_next_phase() - datetime.now(tz=self.tz)).seconds
        hours = int(totalSeconds / 3600)
        minutes = int(totalSeconds % 3600 / 60)
        return hours, minutes

    def get_status(self):
        next_phase = self.get_next_phase()
        for tup in self.sched[next_phase.isoweekday()]:
            if tup[0] == next_phase.timetz():
                return tup[1]


class DiscordTimers(Cog):
    def __init__(self, client):
        self.bot = client
        self.timers = {}

    @loop(minutes=5)  # rate limit: 2 updates per 10 mins
    async def update_channel(self):
        for timer, chl_fmt in self.timers.items():
            await self.bot.get_channel(chl_fmt[0]).edit(
                name=chl_fmt[1].format(timer.get_status(), *timer.till_next_phase())
            )

    @Cog.listener()
    async def on_ready(self):
        HI3TZ = timezone("Etc/GMT-1")
        self.timers.update(
            {
                Timer(
                    {
                        1: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
                        4: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
                        6: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
                    },
                    HI3TZ,
                ): (678423053306298389, "🌍{} {}h {}m"),
                Timer(
                    {
                        1: [(time(hour=4), "Ongoing")],
                        2: [(time(hour=4), "Calculating")],
                    },
                    HI3TZ,
                ): (779022842372685854, "👹{} {}h {}m"),
                Timer(
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
                    HI3TZ,
                ): (752382371596206141, "🔥{} {}h {}m"),
                Timer({w: [(time(hour=h, minute=39), None) for h in range(2, 24, 3)] for w in range(1, 8)}): (
                    779019769755861004,
                    "💖Waifus {1}h {2}m",
                ),
            }
        )
        self.update_channel.start()

    def cog_unload(self):
        self.update_channel.cancel()


def setup(client):
    client.add_cog(DiscordTimers(client))
