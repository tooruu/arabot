import functools
import random
import re
from collections.abc import Awaitable, Callable
from typing import TypeVar

from disnake import Message
from disnake.ext import commands
from disnake.utils import async_all

from .bot import Ara

CogMsgListener = TypeVar("CogMsgListener", bound=Callable[[commands.Cog, Message], Awaitable])


class PfxlessOnCooldown(commands.CommandOnCooldown):
    pass


def copy_dpy_attrs_from(donor):
    organs = {
        "__commands_checks__": [],
        "__commands_max_concurrency__": None,
        "__commands_cooldown__": commands.CooldownMapping(None, commands.BucketType.default),
    }

    def transplantation(patient):
        for organ, default in organs.items():
            replacement = getattr(donor, organ, default)
            setattr(patient, organ, replacement)
        return patient

    return transplantation


class pfxless:
    def __init__(self, **attrs):
        regex: str | re.Pattern[str] | None = attrs.get("regex")
        re_flags: int | re.RegexFlag | None = attrs.get("re_flags")
        self.enabled: bool = attrs.get("enabled", True)
        self.chance: float = attrs.get("chance", 1.0)
        self.allow_prefix: bool = attrs.get("allow_prefix", False)
        self.allow_bots: bool = attrs.get("allow_bots", False)
        self.plain_text_only: bool = attrs.get("plain_text_only", True)

        match regex:
            case str() | None:
                self.pattern = regex
                self.re_flags = re_flags if re_flags is not None else re.IGNORECASE
            case re.Pattern(pattern=str(pattern), flags=flags):
                if re_flags:
                    raise TypeError("Cannot process re_flags argument with a compiled pattern")
                self.pattern = pattern
                self.re_flags = flags
            case bytes() | re.Pattern(pattern=bytes()):
                raise TypeError("pattern argument must not be bytes")
            case _:
                raise TypeError("pattern argument must be str or re.Pattern[str]")

    def __call__(self, func: CogMsgListener) -> CogMsgListener:
        if self.pattern is None:
            self.pattern = rf"\b{func.__name__.replace('_', ' ')}\b"

        if self.plain_text_only:
            self.pattern = rf"(?<![:\w])(?:{self.pattern})(?![:\w])"  # TODO: exclude mentions too

        self.event = self.wrap_callback(func)
        return self.event

    def wrap_callback(self, coro: CogMsgListener) -> CogMsgListener:
        @commands.Cog.listener("on_message")
        @functools.wraps(coro)
        @copy_dpy_attrs_from(coro)
        async def wrapper(cog: commands.Cog, msg: Message) -> None:
            if not (wrapper.enabled and await self.prepare(cog.ara, msg)):
                return
            try:
                await coro(cog, msg)
            finally:
                if wrapper.__commands_max_concurrency__:
                    await wrapper.__commands_max_concurrency__.release(msg)

        wrapper.enabled = self.enabled
        return wrapper

    async def prepare(self, ara: Ara, msg: Message) -> bool:
        return (
            await self._check_message(msg, functools.partial(ara.command_prefix, ara))
            and await self._run_checks(msg)
            and await self._check_concurrency(msg)
            and self._check_cooldown(msg)
            and self.chance > random.random()
        )

    async def _check_message(
        self, msg: Message, pfx_factory: Callable[[Message], Awaitable]
    ) -> bool:
        return (
            (self.allow_prefix or not await pfx_factory(msg))
            and (self.allow_bots or not msg.author.bot)
            and re.search(self.pattern, msg.content, self.re_flags)
        )

    async def _run_checks(self, msg: Message) -> bool:
        return await async_all(check(msg) for check in self.event.__commands_checks__)

    async def _check_concurrency(self, msg: Message) -> bool:
        if not self.event.__commands_max_concurrency__:
            return True
        try:
            await self.event.__commands_max_concurrency__.acquire(msg)
        except commands.MaxConcurrencyReached:
            return False
        return True

    def _check_cooldown(self, msg: Message) -> bool:
        if not self.event.__commands_cooldown__.valid:
            return True
        dt = (msg.edited_at or msg.created_at).timestamp()
        return not self.event.__commands_cooldown__.update_rate_limit(msg, dt)
