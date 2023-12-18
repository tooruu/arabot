import logging
from asyncio import sleep
from datetime import UTC, datetime, time, timedelta, tzinfo
from functools import partial
from zoneinfo import ZoneInfo

from disnake import HTTPException
from disnake.ext.tasks import loop

from arabot.core import Ara, Cog
from arabot.utils import strfdelta

MHYEUTZ = ZoneInfo("Etc/GMT-1")
HYLTZ = ZoneInfo("Etc/GMT-8")


class Timer:
    def __init__(self, schedule: dict[int, list[tuple[time, str]]], tz: tzinfo = UTC):
        self.sched = {
            wkday: sorted((t.replace(tzinfo=tz), s) for t, s in times)
            for wkday, times in sorted(schedule.items())
        }
        self.tznow = partial(datetime.now, tz)

    @property
    def next_phase(self) -> datetime:
        cur_datetime = self.tznow()
        cur_weekday = cur_datetime.isoweekday()
        cur_date = cur_datetime.date()
        event_weekdays = list(self.sched.keys())
        if cur_weekday in event_weekdays:
            cur_time = cur_datetime.timetz()
            for event_time, _ in self.sched[cur_weekday]:
                if cur_time < event_time:
                    return datetime.combine(cur_date, event_time)
        for event_weekday in event_weekdays:
            if cur_weekday < event_weekday:
                next_weekday_date = cur_date + timedelta(days=event_weekday - cur_weekday)
                return datetime.combine(next_weekday_date, self.sched[event_weekday][0][0])
        first_event_date = cur_date + timedelta(days=(event_weekdays[0] - cur_weekday) % 7 or 7)
        first_event_time = next(iter(self.sched.values()))[0][0]
        return datetime.combine(first_event_date, first_event_time)

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
        Timer({1: [(time(hour=4), "Open"), (time(hour=10), "Closed")]}, MHYEUTZ),
    ),
    940719703825993738: ("Bosses🥵{1}", Timer({1: [(time(hour=4), None)]}, MHYEUTZ)),
    904642451887783956: ("HoYoLAB🌟{1}", Timer({w: [(time(), None)] for w in range(1, 8)}, HYLTZ)),
    779019769755861004: (
        "Waifus reset💖{1}",
        Timer({w: [(time(hour=h, minute=39), None) for h in range(2, 24, 3)] for w in range(1, 8)}),
    ),
    1149235203450097694: (
        "Claim reset💖{1}",
        Timer({w: [(time(hour=h, minute=54), None) for h in range(2, 24, 3)] for w in range(1, 8)}),
    ),
}


class ChannelTimers(Cog):
    def __init__(self, ara: Ara):
        self.ara = ara
        self.update_channels.start()

    @loop(minutes=5, seconds=10)  # Rate limit: 2 updates per 10 mins
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
            await sleep(1)

    @update_channels.before_loop
    async def ensure_ready(self):
        await self.ara.wait_until_ready()

    def cog_unload(self):
        self.update_channels.cancel()


def setup(ara: Ara):
    ara.add_cog(ChannelTimers(ara))
