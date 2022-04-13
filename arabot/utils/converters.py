from __future__ import annotations

import re
from string import whitespace

import disnake
from aiohttp import ClientSession
from disnake.ext import commands
from disnake.utils import find

__all__ = (
    "AnyChl",
    "AnyEmoji",
    "AnyMember",
    "AnyRole",
    "AnyTChl",
    "AnyVChl",
    "CslsEmoji",
    "CslsMember",
    "CslsRole",
    "CslsTChl",
    "CslsVChl",
    "Empty",
    "Twemoji",
    "Codeblocks",
)


class Twemoji(commands.Converter):
    base_url = "https://twemoji.maxcdn.com/v/latest/72x72/{}.png"

    def __init__(self, emoji: str):
        self.emoji = emoji
        self.codepoint = "-".join(f"{ord(char):x}" for char in emoji)
        self.url = self.base_url.format(self.codepoint)
        self.name = self.codepoint

    def __str__(self):
        return self.emoji

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> Twemoji:
        emoji = cls(argument)
        if await emoji.read(session=ctx.bot.session, ensure_only=True):
            return emoji
        raise commands.EmojiNotFound(argument)

    async def read(
        self,
        *,
        session: ClientSession = None,
        ensure_only: bool = False,
    ) -> bytes | bool:
        async with (session or ClientSession()).get(self.url) as resp:
            return (True if ensure_only else await resp.read()) if resp.ok else False


class CslsMember(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.Member:
        if found := find(
            lambda member: argument.casefold() in member.display_name.casefold(), ctx.guild.members
        ) or find(lambda member: argument.casefold() in member.name.casefold(), ctx.guild.members):
            return found
        raise commands.MemberNotFound(argument)


class CslsEmoji(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.Emoji:
        guilds = ctx.bot.guilds
        # Put ctx.guild in the start
        guilds.insert(0, guilds.pop(guilds.index(ctx.guild)))
        for guild in guilds:
            if emoji := find(
                lambda emoji: argument.lower() in emoji.name.lower() or argument == str(emoji.id),
                guild.emojis,
            ):
                return emoji
        raise commands.EmojiNotFound(argument)


class CslsTChl(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.TextChannel:
        if found := find(
            lambda chl: argument.casefold() in chl.name.casefold(), ctx.guild.text_channels
        ):
            return found
        raise commands.ChannelNotFound(argument)


class CslsVChl(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.VoiceChannel:
        if found := find(
            lambda chl: argument.casefold() in chl.name.casefold(), ctx.guild.voice_channels
        ):
            return found
        raise commands.ChannelNotFound(argument)


class CslsRole(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> disnake.Role:
        if found := find(lambda role: argument.casefold() in role.name.casefold(), ctx.guild.roles):
            return found
        raise commands.RoleNotFound(argument)


class Empty(commands.Converter):
    async def convert(*_) -> None:
        return None


class Codeblocks(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> list[tuple[str, str]]:
        blocks = re.findall(r"```(?:([+\w-]+)\n+|\n*)(.*?)\n*```|`(.*?)`", argument, re.DOTALL)
        return [
            (lang, (codeblock or inlineblock).strip(whitespace))
            for lang, codeblock, inlineblock in blocks
        ]


AnyMember = disnake.Member | CslsMember | Empty
AnyEmoji = disnake.Emoji | disnake.PartialEmoji | CslsEmoji | Twemoji | Empty
AnyTChl = disnake.TextChannel | CslsTChl | Empty
AnyVChl = disnake.VoiceChannel | CslsVChl | Empty
AnyChl = AnyTChl | AnyVChl | Empty
AnyRole = disnake.Role | CslsRole | Empty
