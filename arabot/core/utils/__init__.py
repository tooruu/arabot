import os
import platform
import sys
from contextlib import _RedirectStream, contextmanager
from datetime import timedelta

import arabot
import disnake

from .checks import *
from .converters import *
from .formatting import *


def system_info() -> str:
    match platform.system():
        case "Windows":
            os_info = platform.uname()
            os_ver = f"{os_info.system} {os_info.release} (version {os_info.version})"
        case "Darwin":
            os_info = platform.mac_ver()
            os_ver = f"Mac OSX {os_info[0]} {os_info[1]}"
        case "Linux":
            try:
                # pyright: reportMissingImports=false
                # pylint: disable=import-outside-toplevel
                import distro
            except ModuleNotFoundError:
                os_info = platform.uname()
                os_ver = f"{os_info[0]} {os_info[2]}"
            else:
                os_info = distro.linux_distribution()
                os_ver = f"{os_info[0]} {os_info[1]}"
        case _:
            os_info = platform.uname()
            os_ver = f"{os_info[0]} {os_info[2]}"

    return f"""Debug Info:

OS version: {os_ver.strip()}
Python executable: {sys.executable}
Python version: {sys.version}
{disnake.__title__.title()} version: {disnake.__version__}
Bot version: {arabot.__version__}
"""


class MissingEnvVar(Exception):
    def __init__(self, key_name):
        super().__init__(f"Couldn't retrieve {key_name!r} from environment")
        self.key_name = key_name


def getkeys(*key_names) -> tuple[str]:
    keys = []
    for key_name in key_names:
        if not (key := os.getenv(key_name)):
            raise MissingEnvVar(key_name)
        keys.append(key)
    return tuple(keys)


class Lockable:
    @contextmanager
    def lock(self, **overwrites):
        """Sets overwrites on self and then resets to initial state"""
        backup = self.__dict__.copy()
        self.__dict__.update(overwrites)
        try:
            yield
        finally:
            for key in overwrites:
                if key in backup:
                    setattr(self, key, backup[key])
                elif hasattr(self, key):
                    delattr(self, key)


class stdin_from(_RedirectStream):  # noqa: N801
    _stream = "stdin"


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
    return time_left
