import logging
import sys
from asyncio import set_event_loop_policy
from importlib.util import find_spec

import disnake
from aiohttp import ClientConnectorError

from . import TESTING, Ara
from .core import LocalizationStore, StderrHandler, StdoutHandler

if find_spec("uvloop"):
    from uvloop import EventLoopPolicy  # type: ignore[import-not-found]
elif find_spec("winloop"):
    from winloop import EventLoopPolicy  # type: ignore[import-not-found]
else:
    from asyncio import DefaultEventLoopPolicy as EventLoopPolicy


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
        activity=disnake.Activity(type=disnake.ActivityType.competing, name="a hackathon!"),
        allowed_mentions=disnake.AllowedMentions.none(),
        case_insensitive=True,
        embed_color=0xE91E63,
        intents=intents,
        localization_provider=LocalizationStore(strict=True, fallback=disnake.Locale.en_US),
        max_messages=10_000,
    )
    if TESTING:
        default_kwargs.update(
            reload=True,
            test_guilds=[954134299119091772],
        )

    return Ara(*args, **default_kwargs | kwargs)


def main() -> bool:
    setup_logging(logging.WARNING)
    set_event_loop_policy(EventLoopPolicy())

    ara = create_ara()
    try:
        ara.run()
    except (ClientConnectorError, disnake.LoginFailure):
        return False
    return True


if __name__ == "__main__":
    sys.exit(not main())
