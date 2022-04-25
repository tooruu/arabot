import os
import platform
import sys
from collections.abc import Generator
from contextlib import _RedirectStream, contextmanager
from glob import glob
from pathlib import Path
from pkgutil import iter_modules

import disnake
from disnake.ext import commands

__all__ = (
    "BOT_VERSION",
    "DEBUG",
    "Color",
    "CustomEmoji",
    "system_info",
    "is_in_guild",
    "MissingEnvVar",
    "getkeys",
    "Lockable",
    "stdin_from",
    "search_directory",
)

DEBUG = bool(os.getenv("debug"))
BOT_VERSION = "5.3.0"
if DEBUG:
    BOT_VERSION += " (DEBUG MODE)"


class Color:
    # red = Colour.from_rgb(218, 76, 82)
    # yellow = Colour.from_rgb(254, 163, 42)
    # green = Colour.from_rgb(39, 159, 109)
    blurple = disnake.Colour.from_rgb(88, 101, 242)
    green = disnake.Colour.from_rgb(87, 242, 135)
    yellow = disnake.Colour.from_rgb(254, 231, 92)
    fuchsia = disnake.Colour.from_rgb(235, 69, 158)
    red = disnake.Colour.from_rgb(237, 66, 69)
    black = disnake.Colour.from_rgb(35, 39, 42)


class CustomEmoji:
    DIO = "<:KonoDioDa:937687826693251102>"
    TERICELEBRATE = "<:TeriCelebrate:937695453506596906>"
    FUKAWHY = "<:FukaWhy:937695447626182676>"
    TOORUWEARY = "<:TooruWeary:937695447487774743>"
    KANNAPAT = "<:KannaPat:937695447718453248>"
    MEISTARE = "<:MeiStare:937695447932370994>"


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
Bot version: {BOT_VERSION}
"""


def is_in_guild(guild_id):
    async def predicate(ctx):
        return ctx.guild and ctx.guild.id == guild_id

    return commands.check(predicate)


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


def search_directory(path) -> Generator[str, None, None]:
    path = Path(path)

    if ".." in os.path.relpath(path):
        raise ValueError("Paths outside the cwd are not supported")
    if not path.exists():
        raise ValueError(f"Provided path '{path.resolve()}' does not exist")
    if not path.is_dir():
        raise ValueError(f"Provided path '{path.resolve()}' is not a directory")

    with_prefix = lambda f: ".".join((path / f).parts)

    modules, packages = set(), set()
    for _, name, ispkg in iter_modules([str(path)]):
        if not name.startswith("_"):
            (packages if ispkg else modules).add(name)
    dirs = {dir.rstrip(os.sep) for dir in glob("[!_]*/", root_dir=path)} - packages

    yield from map(with_prefix, modules)
    yield from map(with_prefix, packages)
    for dir in dirs:
        yield from search_directory(path / dir)
