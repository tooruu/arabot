import logging
import sys
from asyncio import set_event_loop
from contextlib import suppress

import disnake
from aiohttp import ClientConnectorError

from arabot.core import Ara, Config, LocalizationStore, new_event_loop
from arabot.core.logging import StderrHandler, StdoutHandler


def setup_logging(level: int) -> None:
    handlers = [StderrHandler()]
    if level < logging.WARNING:
        handlers.append(StdoutHandler(level))

    logging.basicConfig(
        format="%(asctime)s|%(levelname)8s|%(message)s",
        level=logging.NOTSET,
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        handlers=handlers,
    )


def create_ara(*args, **kwargs) -> Ara:
    intents = disnake.Intents(
        expressions=True,
        guild_messages=True,
        guild_reactions=True,
        guilds=True,
        members=True,
        message_content=True,
        presences=True,
        voice_states=True,
    )
    default_kwargs = dict(
        activity=disnake.Activity(type=disnake.ActivityType.watching, name="727🎪"),
        allowed_mentions=disnake.AllowedMentions.none(),
        case_insensitive=True,
        embed_color=0xE91E63,
        intents=intents,
        localization_provider=LocalizationStore(strict=True, fallback=disnake.Locale.en_US),
        max_messages=10_000,
    )
    if Config.debug_mode:
        default_kwargs.update(
            reload=True,
            test_guilds=[954134299119091772],
        )

    return Ara(*args, **default_kwargs | kwargs)


def main() -> int:
    setup_logging(logging.INFO if Config.debug_mode else logging.WARNING)
    set_event_loop(loop := new_event_loop())

    with suppress(OSError):
        # ctypes.util.find_library doesn't work on Alpine Linux
        disnake.opus.load_opus("libopus.so.0")

    ara = create_ara(loop=loop)
    try:
        ara.run()
    except ClientConnectorError, disnake.LoginFailure:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
