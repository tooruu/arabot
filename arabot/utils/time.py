from datetime import timedelta

from disnake import utils


def strfdelta(delta: timedelta) -> str:
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


def time_in(seconds: float, fmt: str = "R") -> str:
    return utils.format_dt(utils.utcnow() + timedelta(seconds=seconds), fmt)
