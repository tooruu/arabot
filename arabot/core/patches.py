from __future__ import annotations

import logging
import re
from asyncio import sleep
from collections.abc import Iterable

import aiohttp
import disnake
from disnake.ext import commands

from .enums import Category
from .utils import getkeys

__all__ = [
    "Context",
    "Cog",
]


async def temp_channel_mute_message_author(
    self: disnake.Message | Context, duration: float = 60.0, reason: str | None = None
):
    await self.channel.temp_mute_member(self.author, duration, reason)


class Context(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ara: commands.Bot = self.bot

    async def reply(
        self, content: str | None = None, *, strict: bool = False, **kwargs
    ) -> disnake.Message:
        reply = super().reply(content, **kwargs)

        if strict:
            return await reply

        try:
            return await reply
        except disnake.HTTPException:
            return await self.send(content, **kwargs)

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

        if msg.reference:
            ref = msg.reference.cached_message or msg.reference.resolved
            if isinstance(ref, disnake.Message):
                ref_ctx = await self.ara.get_context(ref)
                return await ref_ctx._rsearch(target)

        return None

    async def tick(self) -> bool:
        try:
            await self.message.add_reaction("✅")
        except (disnake.HTTPException, disnake.Forbidden):
            return False
        return True

    temp_channel_mute_author = temp_channel_mute_message_author

    def reset_cooldown(self) -> bool:
        if not self.command:
            return False
        self.command.reset_cooldown(self)
        return True


class Cog(commands.Cog):
    def __init_subclass__(cls, category: Category = None, keys: Iterable[str] = (), **kwargs):
        cls.category = category
        for key_name, key in zip(keys, getkeys(*keys)):
            setattr(cls, key_name, key)
        super().__init_subclass__(**kwargs)


async def get_unlimited_invite(self: disnake.Guild) -> str | None:
    for i in await self.invites():
        if i.max_age == 0 and i.max_uses == 0:
            return i.url


async def temp_mute_channel_member(
    self: disnake.abc.Messageable,
    member: disnake.Member,
    duration: float = 60.0,
    reason: str | None = None,
):
    old_perms = self.overwrites_for(member)
    temp_perms = self.overwrites_for(member)
    temp_perms.send_messages = False
    try:
        await self.set_permissions(member, overwrite=temp_perms, reason=reason)
        await sleep(duration)
    finally:
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
        logging.warning(f"Could not connect to voice channel {self!r}")
        return

    disconnect = lambda _: vc.loop.create_task(vc.disconnect(force=force_disconnect))
    vc.play(audio, after=disconnect)


aiohttp.ClientSession.fetch_json = fetch_json
disnake.Guild.get_unlimited_invite = get_unlimited_invite
disnake.abc.Messageable.temp_mute_member = temp_mute_channel_member
disnake.VoiceChannel.connect_play_disconnect = connect_play_disconnect
disnake.Asset.compat = property(lambda self: self.with_static_format("png"))
disnake.Message.temp_channel_mute_author = temp_channel_mute_message_author
