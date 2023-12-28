import logging
import re

import disnake

from . import TESTING, Ara
from .core import LocalizationStore


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s|%(levelname)s|%(message)s",
        level=logging.INFO if TESTING else logging.WARNING,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def prefix_manager(ara: Ara, msg: disnake.Message) -> str | None:
    custom_prefix = await ara.db.get_guild_prefix(msg.guild.id) or ";"
    pfx_pattern = (
        rf"{re.escape(custom_prefix)}\s*|ara\s+|<@(?:!?{ara.user.id}|&{msg.guild.self_role.id})>\s*"
    )
    return (found := re.match(pfx_pattern, msg.content, re.IGNORECASE)) and found[0]


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
        localization_provider=LocalizationStore(strict=True, fallback=disnake.Locale.en_US),
        max_messages=10_000,
    )
    if TESTING:
        default_kwargs.update(
            reload=True,
            test_guilds=[954134299119091772],
        )

    return Ara(*args, **default_kwargs | kwargs)


def main() -> None:
    setup_logging()
    create_ara().run()


if __name__ == "__main__":
    main()
