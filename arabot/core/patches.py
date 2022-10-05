from __future__ import annotations

import logging
import re
from asyncio import sleep
from collections.abc import Awaitable, Callable, Iterable
from contextlib import suppress
from functools import partial, partialmethod
from typing import Literal

import aiohttp
import disnake
from disnake.ext import commands

from ..utils import fullqualname, getkeys
from .enums import Category

__all__ = [
    "Context",
    "Cog",
    "LocalizationStore",
]


class Context(commands.Context):
    bot: commands.Bot

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ara: commands.Bot = self.bot

    @property
    def argument_only(self) -> str:
        if not self.valid:
            return self.message.content

        content = self.message.content
        for p in self.prefix, *self.invoked_parents, self.invoked_with:
            content = content.removeprefix(p).lstrip()
        return content

    async def rsearch(self, target: Literal["content", "image_url"]) -> str | None:
        if target == "content":
            self.message.content = ""  # We don't need current message's content
        return await self._rsearch(target)

    async def _rsearch(self, target: str) -> str | None:
        msg = self.message
        result = None
        match target:
            case "content":
                result = self.argument_only

            case "image_url":
                if attachment := disnake.utils.find(
                    lambda a: a.content_type.startswith("image") and a.height, msg.attachments
                ):
                    result = attachment.url
                elif embed := disnake.utils.find(lambda e: e.image.url, msg.embeds):
                    result = embed.image.url
                elif re.fullmatch(r"https?://(-\.)?([^\s/?\.#]+\.?)+(/\S*)?", self.argument_only):
                    result = self.argument_only
                elif msg.stickers:
                    result = msg.stickers[0].url

        if result:
            return result

        if ref_msg := await self.get_or_fetch_reference_message():
            ref_ctx = await self.bot.get_context(ref_msg)
            return await ref_ctx._rsearch(target)

        return None

    tick = property(lambda self: self.message.tick)
    blue_tick = property(lambda self: self.message.blue_tick)

    def reset_cooldown(self) -> bool:
        if not self.command:
            return False
        self.command.reset_cooldown(self)
        return True

    reply_ping = partialmethod(
        commands.Context.reply, allowed_mentions=disnake.AllowedMentions.all()
    )
    send_ping = partialmethod(commands.Context.send, allowed_mentions=disnake.AllowedMentions.all())

    temp_channel_mute_author = property(lambda self: self.message.temp_channel_mute_author)

    async def get_or_fetch_reference_message(self) -> disnake.Message | False | None:
        return await self.message.get_or_fetch_reference_message()

    getch_reference_message = get_or_fetch_reference_message

    def l10n_from_guild_locale(self, key: str, scope_depth: int = 1) -> str | None:
        return self.ara.i18n.getl(key, self.guild.preferred_locale, scope_depth + (scope_depth > 0))

    _ = l10n_from_guild_locale

    def send_(self, content: str, autofill: bool = True, **kwargs) -> Awaitable[disnake.Message]:
        return self.send(self._(content, autofill + autofill), **kwargs)

    def reply_(self, content: str, autofill: bool = True, **kwargs) -> Awaitable[disnake.Message]:
        return self.reply(self._(content, autofill + autofill), **kwargs)

    def send_ping_(
        self, content: str, autofill: bool = True, **kwargs
    ) -> Awaitable[disnake.Message]:
        return self.send_ping(self._(content, autofill + autofill), **kwargs)

    def reply_ping_(
        self, content: str, autofill: bool = True, **kwargs
    ) -> Awaitable[disnake.Message]:
        return self.reply_ping(self._(content, autofill + autofill), **kwargs)


class Cog(commands.Cog):
    def __init_subclass__(
        cls, category: Category = Category.NO_CATEGORY, keys: Iterable[str] = (), **kwargs
    ):
        cls.category = category
        for key_name, key in zip(keys, getkeys(*keys)):
            setattr(cls, key_name, key)
        super().__init_subclass__(**kwargs)


class LocalizationStore(disnake.LocalizationStore):
    def __init__(self, *, strict: bool, fallback: disnake.Locale | None = None):
        self.fallback = fallback
        super().__init__(strict=strict)

    def getl(self, key: str, locale: disnake.Locale, scope_depth: int = 1) -> str | None:
        """Returns localized string for a given locale and key combination.
        Uses `self.fallback` locale if it is set and given :param:`locale` doesn't exist.

        :param key: L10n key
        :type key: str
        :param locale: L10n locale
        :type locale: disnake.Locale
        :param scope_depth: Call stack depth of the scope whose qualified name will be used for
            autofilling :param:`key`. If `0`, autofill is disabled. Defaults to `1`.
        :type scope_depth: int
        :raises disnake.LocalizationKeyError: Raise if key doesn't exist and `self.strict` is `True`
        :return: Localized string. Can be `None` if `self.strict` is `False`.
        :rtype: str, optional
        """
        if "." not in key:
            key = fullqualname(key, depth=scope_depth + 1) if scope_depth > 0 else f"generic.{key}"
        l10n_data = self._loc.get(key, {})
        localized = l10n_data.get(locale.value)
        if localized is None:
            if self.fallback:
                localized = l10n_data.get(self.fallback.value)
            if self.fallback is None and self.strict:
                raise disnake.LocalizationKeyError(key)
        return localized


async def get_unlimited_invite_link(self: disnake.Guild) -> str | False | None:
    if self.vanity_url_code:
        return f"https://discord.gg/{self.vanity_url_code}"
    if not self.me.guild_permissions.manage_guild:
        return False
    invites = await self.invites()
    invite = next(filter(lambda i: i.max_age == 0 and i.max_uses == 0, invites), None)
    return str(invite) if invite else None


async def temp_mute_channel_member(
    self: disnake.abc.Messageable,
    member: disnake.Member,
    duration: float = 60.0,
    reason: str | None = None,
    *,
    success_msg: Callable[[], Awaitable] | str | bool = True,
    failure_msg: Callable[[], Awaitable] | str | bool = False,
) -> None:
    old_perms = self.overwrites_for(member)
    temp_perms = self.overwrites_for(member)
    temp_perms.send_messages = False

    try:
        await self.set_permissions(member, overwrite=temp_perms, reason=reason)
        if success_msg:
            if isinstance(success_msg, str):
                success_msg = partial(self.send_ping, success_msg)
            elif success_msg is True:
                success_msg = partial(
                    self.send_ping, f"{member.mention} has been muted for {duration:.0f} seconds"
                )
            await success_msg()
        await sleep(duration)
    except disnake.Forbidden:
        if failure_msg:
            if isinstance(failure_msg, str):
                failure_msg = partial(self.send_ping, failure_msg)
            elif failure_msg is True:
                failure_msg = partial(self.send_ping, f"I lack permission to mute {member.mention}")
            await failure_msg()
    finally:
        with suppress(disnake.Forbidden):
            await self.set_permissions(
                member, overwrite=None if old_perms.is_empty() else old_perms, reason=reason
            )


async def fetch_json(self: aiohttp.ClientSession, url: str, *, method: str = "get", **kwargs):
    async with self.request(method, url, **{"raise_for_status": True, **kwargs}) as resp:
        return await resp.json()


async def connect_play_disconnect(
    self: disnake.VoiceChannel, audio: disnake.AudioSource, *, force_disconnect: bool = False
) -> None:
    try:
        vc = await self.connect()
    except Exception:
        logging.warning("Could not connect to voice channel %r", self)
        return

    disconnect = lambda _: vc.loop.create_task(vc.disconnect(force=force_disconnect))
    vc.play(audio, after=disconnect)


async def get_or_fetch_reference_message(self: disnake.Message) -> disnake.Message | False | None:
    if not (ref := self.reference):
        return False
    with suppress(disnake.HTTPException):
        return ref.cached_message or await self.channel.fetch_message(ref.message_id)
    return None


def embed_with_author(self: disnake.Embed, user: disnake.abc.User) -> disnake.Embed:
    return self.set_author(
        name=user.display_name,
        icon_url=user.display_avatar.as_icon.compat,
        url=f"https://discord.com/users/{user.id}",
    )


def top_perm_role(self: disnake.Member) -> disnake.Role:
    "Get highest role that has at least one permission to exclude dummy roles e.g. colors"
    is_perm_role = lambda r: r.permissions.value != 0
    return next(filter(is_perm_role, reversed(self.roles)), self.guild.default_role)


@property
def presence_count(self: disnake.Guild) -> int:
    if self.approximate_presence_count is not None:
        return self.approximate_presence_count
    return sum(m.status is not disnake.Status.offline for m in self.members)


async def message_green_tick(self: disnake.Message) -> bool:
    try:
        await self.add_reaction("✅")
    except (disnake.HTTPException, disnake.Forbidden):
        return False
    return True


async def message_blue_tick(self: disnake.Message) -> bool:
    try:
        await self.add_reaction("☑️")
    except (disnake.HTTPException, disnake.Forbidden):
        return False
    return True


aiohttp.ClientSession.fetch_json = fetch_json
disnake.abc.Messageable.send_ping = disnake.Webhook.send_ping = property(
    lambda self: partial(self.send, allowed_mentions=disnake.AllowedMentions.all())
)
disnake.abc.Messageable.temp_mute_member = temp_mute_channel_member
disnake.Asset.as_icon = property(lambda self: self.with_size(32))
disnake.Asset.compat = property(lambda self: self.with_static_format("png"))
disnake.Asset.maxres = property(lambda self: self.with_size(4096))
disnake.Embed.with_author = embed_with_author
disnake.Guild.get_unlimited_invite_link = get_unlimited_invite_link
disnake.Guild.presence_count = presence_count
disnake.Interaction.l10n_from_guild_locale = disnake.Interaction._ = Context.l10n_from_guild_locale
disnake.Member.top_perm_role = property(top_perm_role)
disnake.Message.get_or_fetch_reference_message = get_or_fetch_reference_message
disnake.Message.getch_reference_message = get_or_fetch_reference_message
disnake.Message.reply = partialmethod(disnake.Message.reply, fail_if_not_exists=False)
disnake.Message.reply_ping = partialmethod(
    disnake.Message.reply, allowed_mentions=disnake.AllowedMentions.all()
)
disnake.Message.temp_channel_mute_author = property(
    lambda self: partial(self.channel.temp_mute_member, self.author)
)
disnake.Message.blue_tick = message_blue_tick
disnake.Message.tick = message_green_tick
disnake.VoiceChannel.connect_play_disconnect = connect_play_disconnect
