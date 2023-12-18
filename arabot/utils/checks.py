from collections.abc import Callable, Coroutine
from typing import TypeVar

import disnake
from disnake.ext import commands

__all__ = [
    "author_in_voice_channel",
    "bot_not_speaking_in_guild",
    "can_someone_hear_in_author_channel",
    "is_in_guild",
]
Command = TypeVar("Command", commands.Command, Callable[..., Coroutine])


def is_in_guild(guild_id: int) -> Command:
    return commands.check(lambda ctx: ctx.guild and ctx.guild.id == guild_id)


def bot_not_speaking_in_guild(func: Command) -> Command:
    return commands.check(lambda ctx: not ctx.guild.voice_client)(func)


def author_in_voice_channel(func: Command) -> Command:
    return commands.check(lambda ctx: getattr(ctx.author.voice, "channel", None))(func)


def can_someone_hear_in_author_channel(func: Command) -> Command:
    def predicate(ctx: commands.Context | disnake.Message) -> bool:
        return any(
            not (m.bot or m.voice.deaf or m.voice.self_deaf)
            for m in ctx.author.voice.channel.members
        )

    return commands.check(predicate)(func)
