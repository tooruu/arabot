from discord.utils import find
from discord.ext.commands import (
    MemberConverter,
    EmojiConverter,
    PartialEmojiConverter,
    TextChannelConverter,
    VoiceChannelConverter,
    RoleConverter,
    Converter,
)
from ..helpers.finder import Finder


class FindMember(Finder, MemberConverter):
    @staticmethod
    async def find(ctx, argument):
        result = find(lambda member: argument.lower() in member.display_name.lower(), ctx.guild.members)
        return result or find(lambda member: argument.lower() in member.name.lower(), ctx.guild.members)


class FindEmoji(Finder, EmojiConverter, PartialEmojiConverter):
    @staticmethod
    async def find(ctx, argument):
        ctx.bot.guilds.insert(0, ctx.bot.guilds.pop(ctx.bot.guilds.index(ctx.guild)))
        for guild in ctx.bot.guilds:
            if emote := find(
                lambda emoji: argument.lower() in emoji.name.lower() or argument.lower() == str(emoji.id), guild.emojis
            ):
                return emote
        if len(argument) == 1:
            return f"https://raw.githubusercontent.com/astronautlevel2/twemoji/gh-pages/128x128/{ord(argument):x}.png"


class FindTxChl(Finder, TextChannelConverter):
    @staticmethod
    async def find(ctx, argument):
        return find(lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.text_channels)


class FindVcChl(Finder, VoiceChannelConverter):
    @staticmethod
    async def find(ctx, argument):
        return find(lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.voice_channels)


class FindChl(Finder, TextChannelConverter, VoiceChannelConverter):
    @staticmethod
    async def find(ctx, argument):
        return find(
            lambda chl: chl.name.lower().startswith(argument.lower()),
            ctx.guild.text_channels + ctx.guild.voice_channels,
        )


class FindRole(Finder, RoleConverter):
    @staticmethod
    async def find(ctx, argument):
        return lambda role: role.name.lower().startswith(argument.lower()), ctx.guild.roles


class ChlMemberConverter(Converter):
    async def convert(self, ctx, argument):
        result = find(lambda member: argument.lower() in member.display_name.lower(), ctx.channel.members)
        return result or find(lambda member: argument.lower() in member.name.lower(), ctx.channel.members)
