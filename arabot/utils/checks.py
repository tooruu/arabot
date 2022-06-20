import disnake as _disnake
from disnake.ext import commands as _commands


def is_in_guild(guild_id: int):
    return _commands.check(lambda ctx: ctx.guild and ctx.guild.id == guild_id)


def bot_not_speaking_in_guild(func):
    return _commands.check(lambda ctx: not ctx.guild.voice_client)(func)


def author_in_voice_channel(func):
    return _commands.check(lambda ctx: getattr(ctx.author.voice, "channel", None))(func)


def can_someone_hear_in_author_channel(func):
    def predicate(ctx: _commands.Context | _disnake.Message) -> bool:
        return any(
            not (m.bot or m.voice.deaf or m.voice.self_deaf)
            for m in ctx.author.voice.channel.members
        )

    return _commands.check(predicate)(func)
