import asyncio
import logging
import os
import re
import signal

import disnake

from . import TESTING, Ara


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s|%(levelname)s|%(message)s",
        level=logging.INFO if TESTING else logging.WARNING,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def prefix_manager(ara: Ara, msg: disnake.Message) -> str | None:
    pfx_pattern = r"a; *" if TESTING else rf"; *|ara +|<@!?{ara.user.id}> *"
    if found := re.match(pfx_pattern, msg.content, re.IGNORECASE):
        return found[0]


def create_ara(*args, **kwargs) -> Ara:
    intents = disnake.Intents(
        emojis_and_stickers=True,
        guild_messages=True,
        guild_reactions=True,
        guilds=True,
        members=True,
        message_content=True,
        presences=True,
        voice_states=True,
    )
    default_kwargs = dict(
        activity=disnake.Activity(type=disnake.ActivityType.competing, name="McDonalds"),
        allowed_mentions=disnake.AllowedMentions.none(),
        case_insensitive=True,
        command_prefix=prefix_manager,
        embed_color=0xE91E63,
        intents=intents,
        max_messages=10_000,
    )
    if TESTING:
        default_kwargs.update(
            reload=True,
            test_guilds=[954134299119091772, 676889696302792774],
        )

    return Ara(*args, **default_kwargs | kwargs)


def main() -> None:
    setup_logging()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ara = create_ara(loop=loop)

    try:
        for s in signal.SIGINT, signal.SIGTERM:
            loop.add_signal_handler(s, lambda: loop.create_task(ara.close()))
    except NotImplementedError:
        pass

    try:
        loop.run_until_complete(ara.start())
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        loop.run_until_complete(ara.close())
    except Exception:
        logging.critical("Bot has crashed", exc_info=True)
        loop.run_until_complete(ara.close())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        if os.name == "nt" and isinstance(loop, asyncio.ProactorEventLoop):
            loop.run_until_complete(asyncio.sleep(1))  # Fixes RuntimeError on Windows
        asyncio.set_event_loop(None)
        loop.stop()
        loop.close()


if __name__ == "__main__":
    main()
