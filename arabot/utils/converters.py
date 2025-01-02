import re
from collections.abc import Callable, Iterable
from itertools import chain
from string import whitespace
from types import UnionType
from typing import Self

import disnake
from aiohttp import ClientSession
from disnake.ext import commands
from disnake.utils import find

from .regexes import CUSTOM_EMOJI_RE

__all__ = [
    "AnyEmoji",
    "AnyEmojis",
    "AnyGuild",
    "AnyMember",
    "AnyMemberOrUser",
    "AnyMsgChl",
    "AnyRole",
    "AnySound",
    "AnySounds",
    "AnyTxtChl",
    "AnyUser",
    "AnyVcChl",
    "CIEmoji",
    "CIGuild",
    "CIMember",
    "CIRole",
    "CITextChl",
    "CIVoiceChl",
    "Codeblocks",
    "Empty",
    "Twemoji",
    "clean_content",
]


def fuzzy_search(seq: Iterable, attr: str, arg: str) -> Callable:
    arg_ci_re_search = re.compile(re.escape(arg), re.IGNORECASE).search
    return find(lambda obj: arg_ci_re_search(getattr(obj, attr)), seq)


class clean_content(commands.clean_content):  # noqa: N801
    def __init__(self, fix_emojis: bool = True, **kwargs: bool):
        self.fix_emojis = fix_emojis
        super().__init__(**kwargs)

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        argument = await super().convert(ctx, argument)
        return CUSTOM_EMOJI_RE.sub(r"\g<name>", argument) if self.fix_emojis else argument


class Twemoji(commands.Converter):
    base_url = "https://cdn.jsdelivr.net/gh/jdecked/twemoji/assets/72x72/{}.png"

    def __init__(self, emoji: str):
        self.emoji = emoji.removesuffix("\N{VARIATION SELECTOR-16}") if len(emoji) == 2 else emoji
        self.codepoint = "-".join(f"{ord(char):x}" for char in self.emoji)
        self.url = self.base_url.format(self.codepoint)
        self.name = self.codepoint

    def __str__(self) -> str:
        return self.emoji

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> Self:
        emoji = cls(argument)
        if await emoji.read(ctx.bot.session, ensure_only=True):
            return emoji
        raise commands.EmojiNotFound(argument)

    async def read(self, session: ClientSession, *, ensure_only: bool = False) -> bytes | bool:
        async with session.get(self.url) as resp:
            if resp.ok:
                return True if ensure_only else await resp.read()
            return False


class CIMember(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.Member:
        if found := (
            fuzzy_search(ctx.guild.members, "display_name", argument)
            or fuzzy_search(ctx.guild.members, "name", argument)
        ):
            return found
        raise commands.MemberNotFound(argument)


class UserFromCIMember(CIMember):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.User:
        try:
            member = await super().convert(ctx, argument)
        except commands.MemberNotFound:
            raise commands.UserNotFound(argument) from None
        return member._user


class CIEmoji(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.Emoji:
        emojis = chain(ctx.guild.emojis, ctx.bot.emojis)
        if emoji := fuzzy_search(emojis, "name", argument):
            return emoji
        raise commands.EmojiNotFound(argument)


class CITextChl(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.TextChannel:
        if found := fuzzy_search(ctx.guild.text_channels, "name", argument):
            return found
        raise commands.ChannelNotFound(argument)


class CIVoiceChl(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.VoiceChannel:
        if found := fuzzy_search(ctx.guild.voice_channels, "name", argument):
            return found
        raise commands.ChannelNotFound(argument)


class CIRole(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.Role:
        if found := fuzzy_search(ctx.guild.roles, "name", argument):
            return found
        raise commands.RoleNotFound(argument)


class CISound(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.GuildSoundboardSound:
        sounds = chain(ctx.guild.soundboard_sounds, ctx.bot.soundboard_sounds)
        if sound := fuzzy_search(sounds, "name", argument):
            return sound
        raise commands.GuildSoundboardSoundNotFound(argument)


class Empty(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> None:
        return None


class Codeblocks(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> list[tuple[str, str]]:
        blocks: list[str] = re.findall(
            r"```(?:([+\w-]+)\n+|\n*)(.*?)\n*```|`(.*?)`", argument, re.DOTALL
        )
        return [
            (lang, (codeblock or inlineblock).strip(whitespace))
            for lang, codeblock, inlineblock in blocks
        ]


class CIGuild(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.Guild:
        if found := find(ctx.bot.guild, "name", argument):
            return found
        raise commands.GuildNotFound(argument)


AnyMember = disnake.Member | CIMember | Empty
AnyUser = disnake.User | UserFromCIMember | Empty
AnyMemberOrUser = disnake.Member | CIMember | disnake.User | Empty
AnyEmoji = disnake.Emoji | CIEmoji | disnake.PartialEmoji | Twemoji | Empty
AnyTxtChl = disnake.TextChannel | CITextChl | Empty
AnyVcChl = disnake.VoiceChannel | CIVoiceChl | disnake.StageChannel | Empty
AnyMsgChl = disnake.TextChannel | CITextChl | AnyVcChl
AnyRole = disnake.Role | CIRole | Empty
AnyGuild = disnake.Guild | CIGuild | Empty
AnySound = disnake.GuildSoundboardSound | CISound | Empty


async def convert_union[T, T2: str](
    ctx: commands.Context, argument: T2, union: UnionType
) -> T | None:
    converters: tuple[
        type[T | commands.Converter[T]] | commands.Converter[T] | Callable[[T2], T], ...
    ] = union.__args__
    parameter = ctx.current_parameter
    for converter in converters:
        try:
            return await commands.converter._actual_conversion(ctx, converter, argument, parameter)
        except commands.CommandError:
            pass
    return None


class AnyEmojis(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> list[AnyEmoji]:
        argument = argument.replace("<", " <").replace(">", "> ")
        argument = re.sub(r"(?<!<a)(?<!<):(?!\d{17,20}>)", " ", argument, flags=re.ASCII)
        return [await convert_union(ctx, arg, AnyEmoji) for arg in argument.split()]


class AnySounds(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> list[AnySound]:
        return [await convert_union(ctx, arg, AnySound) for arg in argument.split()]
