from __future__ import annotations

import logging
import re
from asyncio import sleep
from collections.abc import Iterable
from contextlib import suppress
from functools import partial, partialmethod
from typing import Awaitable, Callable

import aiohttp
import disnake
from disnake.ext import commands

from .enums import Category
from .utils import getkeys

__all__ = [
    "Context",
    "Cog",
]


class Context(commands.Context):
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

    async def rsearch(self, target: str) -> str | None:
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

        if ref_msg := await self.getch_reference_message():
            ref_ctx = await self.bot.get_context(ref_msg)
            return await ref_ctx._rsearch(target)

        return None

    async def tick(self) -> bool:
        try:
            await self.message.add_reaction("✅")
        except (disnake.HTTPException, disnake.Forbidden):
            return False
        return True

    def reset_cooldown(self) -> bool:
        if not self.command:
            return False
        self.command.reset_cooldown(self)
        return True

    reply_mention = partialmethod(
        commands.Context.reply, allowed_mentions=disnake.AllowedMentions.all()
    )
    send_mention = partialmethod(
        commands.Context.send, allowed_mentions=disnake.AllowedMentions.all()
    )

    temp_channel_mute_author = property(lambda self: self.message.temp_channel_mute_author)

    async def getch_reference_message(self) -> disnake.Message | False | None:
        return await self.message.getch_reference_message()


class Cog(commands.Cog):
    def __init_subclass__(
        cls, category: Category | None = None, keys: Iterable[str] = (), **kwargs
    ):
        cls.category = category
        for key_name, key in zip(keys, getkeys(*keys)):
            setattr(cls, key_name, key)
        super().__init_subclass__(**kwargs)


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
                success_msg = partial(self.send, success_msg)
            elif success_msg is True:
                success_msg = partial(
                    self.send, f"{member.mention} has been muted for {duration:.0f} seconds"
                )
            await success_msg()
        await sleep(duration)
    except disnake.Forbidden:
        if failure_msg:
            if isinstance(failure_msg, str):
                failure_msg = partial(self.send, failure_msg)
            elif failure_msg is True:
                failure_msg = partial(self.send, f"I lack permission to mute {member.mention}")
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


async def getch_reference_message(self: disnake.Message) -> disnake.Message | False | None:
    if not (ref := self.reference):
        return False
    ref_msg = ref.cached_message or ref.resolved or await self.channel.fetch_message(ref.message_id)
    return ref_msg if isinstance(ref_msg, disnake.Message) else None


def embed_with_author(self: disnake.Embed, user: disnake.abc.User) -> disnake.Embed:
    return self.set_author(
        name=user.display_name,
        icon_url=user.display_avatar.as_icon.compat.url,
        url=f"https://discord.com/users/{user.id}",
    )


aiohttp.ClientSession.fetch_json = fetch_json
disnake.abc.Messageable.send_mention = disnake.Webhook.send_mention = property(
    lambda self: partial(self.send, allowed_mentions=disnake.AllowedMentions.all())
)
disnake.abc.Messageable.temp_mute_member = temp_mute_channel_member
disnake.Asset.as_icon = property(lambda self: self.with_size(32))
disnake.Asset.compat = property(lambda self: self.with_static_format("png"))
disnake.Embed.with_author = embed_with_author
disnake.Guild.get_unlimited_invite_link = get_unlimited_invite_link
disnake.Message.getch_reference_message = getch_reference_message
disnake.Message.reply = partialmethod(disnake.Message.reply, fail_if_not_exists=False)
disnake.Message.reply_mention = partialmethod(
    disnake.Message.reply, allowed_mentions=disnake.AllowedMentions.all()
)
disnake.Message.temp_channel_mute_author = property(
    lambda self: partial(self.channel.temp_mute_member, self.author)
)
disnake.VoiceChannel.connect_play_disconnect = connect_play_disconnect
