import os
import platform
import sys
from contextlib import _RedirectStream, contextmanager

import disnake
from arabot import __version__

__all__ = [
    "system_info",
    "MissingEnvVar",
    "getkeys",
    "Lockable",
    "stdin_from",
]


def system_info() -> str:
    match platform.system():
        case "Windows":
            os_info = platform.uname()
            os_ver = "{0.system} {0.release} (version {0.version})".format(os_info)
        case "Darwin":
            os_info = platform.mac_ver()
            os_ver = "Mac OSX {0[0]} {0[1]}".format(os_info)
        case "Linux":
            try:
                import distro  # pyright: reportMissingImports=false
            except ModuleNotFoundError:
                os_info = platform.uname()
                os_ver = "{0[0]} {0[2]}".format(os_info)
            else:
                os_info = distro.linux_distribution()
                os_ver = "{0[0]} {0[1]}".format(os_info)
        case _:
            os_info = platform.uname()
            os_ver = "{0[0]} {0[2]}".format(os_info)

    return f"""Debug Info:

OS version: {os_ver.strip()}
Python executable: {sys.executable}
Python version: {sys.version}
{disnake.__title__.title()} version: {disnake.__version__}
Bot version: {__version__}
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


class stdin_from(_RedirectStream):
    _stream = "stdin"
