import logging
from datetime import datetime, time, timedelta, timezone, tzinfo
from functools import partial
from zoneinfo import ZoneInfo

from disnake import HTTPException
from disnake.ext.tasks import loop

from arabot.core import Ara, Cog
from arabot.utils import strfdelta

MHYEUTZ = ZoneInfo("Etc/GMT-1")
HYLTZ = ZoneInfo("Etc/GMT-8")


class Timer:
    def __init__(self, schedule: dict[int, list[tuple[time, str]]], tz: tzinfo = timezone.utc):
        self.sched = {
            wkday: sorted((t.replace(tzinfo=tz), s) for t, s in times)
            for wkday, times in sorted(schedule.items())
        }
        self.tznow = partial(datetime.now, tz)

    @property
    def next_phase(self) -> datetime:
        cur_time = self.tznow()
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

    @property
    def till_next_phase(self) -> timedelta:
        total_seconds = (self.next_phase - self.tznow()).total_seconds()
        return timedelta(seconds=total_seconds)

    @property
    def status(self) -> str | None:
        next_phase = self.next_phase
        return next(
            status_name
            for when, status_name in self.sched[next_phase.isoweekday()]
            if when == next_phase.timetz()
        )


timers: dict[int, tuple[str, Timer]] = {
    678423053306298389: (
        "OW🌍{} {}",
        Timer(
            {
                1: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
                4: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
                6: [(time(hour=3), "Ongoing"), (time(hour=4), "Finalizing")],
            },
            MHYEUTZ,
        ),
    ),
    752382371596206141: (
        "Abyss🔥{} {}",
        Timer(
            {
                1: [(time(hour=15), "Preparing")],
                3: [(time(hour=22), "Ongoing"), (time(hour=22, minute=30), "Finalizing")],
                5: [(time(hour=15), "Preparing")],
                7: [(time(hour=22), "Ongoing"), (time(hour=22, minute=30), "Finalizing")],
            },
            MHYEUTZ,
        ),
    ),
    779022842372685854: (
        "MA👹{} {}",
        Timer(
            {
                1: [(time(hour=4), "Ongoing")],
                2: [(time(hour=4), "Calculating")],
            },
            MHYEUTZ,
        ),
    ),
    1036564782091866193: (
        "ER🔮{} {}",
        Timer(
            {
                1: [(time(hour=4), "Open"), (time(hour=10), "Closed")],
            },
            MHYEUTZ,
        ),
    ),
    940719703825993738: ("Bosses🥵{1}", Timer({1: [(time(hour=4), None)]}, MHYEUTZ)),
    904642451887783956: (
        "HoYoLAB🌟{1}",
        Timer({w: [(time(), None)] for w in range(1, 8)}, HYLTZ),
    ),
    779019769755861004: (
        "Waifus reset💖{1}",
        Timer({w: [(time(hour=h, minute=39), None) for h in range(2, 24, 3)] for w in range(1, 8)}),
    ),
}


class ChannelTimers(Cog):
    def __init__(self, ara: Ara):
        self.ara = ara
        self.update_channels.start()

    @loop(minutes=5)  # Rate limit: 2 updates per 10 mins
    async def update_channels(self):
        for chl_id, fmt, timer in [(cid, *timer_info) for cid, timer_info in timers.items()]:
            if not (channel := self.ara.get_channel(chl_id)):
                logging.warning("Timer channel %r not found", chl_id)
                del timers[chl_id]
                continue

            time_left = strfdelta(timer.till_next_phase)
            updated_channel_name = fmt.format(timer.status, time_left)
            try:
                await channel.edit(name=updated_channel_name)
            except HTTPException as exc:
                logging.warning("Failed to update timer channel %r: %s", chl_id, exc)

    @update_channels.before_loop
    async def ensure_ready(self):
        await self.ara.wait_until_ready()

    def cog_unload(self):
        self.update_channels.cancel()


def setup(ara: Ara):
    ara.add_cog(ChannelTimers(ara))
