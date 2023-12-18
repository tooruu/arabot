import typing as _t
from datetime import timedelta as _timedelta

from disnake import utils as _utils

DiscordDT = _t.NewType("DiscordDT", str)


def strfdelta(delta: _timedelta) -> str:
    days = delta.days
    hours = delta.seconds // 3600
    minutes = delta.seconds % 3600 // 60
    time_left = ""
    if days:
        time_left += f"{days}d "
    if hours:
        time_left += f"{hours}h"
    if not days:
        time_left += f" {minutes}m"
    return time_left.strip()


def time_in(seconds: float, fmt: str = "R") -> DiscordDT:
    return _utils.format_dt(_utils.utcnow() + _timedelta(seconds=seconds), fmt)
