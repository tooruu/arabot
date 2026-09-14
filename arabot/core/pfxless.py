import functools
import random
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from disnake import Message
from disnake.ext import commands
from disnake.utils import async_all

if TYPE_CHECKING:
    from numbers import Number

    from arabot.core.bot import Ara

type CogMsgListener = Callable[[commands.Cog, Message], Awaitable]


class PfxlessOnCooldown(commands.CommandOnCooldown):
    pass


def copy_dpy_attrs_from[T: CogMsgListener](donor: T) -> Callable[[T], T]:
    organs = {
        "__commands_checks__": [],
        "__commands_max_concurrency__": None,
        "__commands_cooldown__": commands.CooldownMapping(None, commands.BucketType.default),
    }

    def transplantation(patient: T) -> T:
        for organ, default in organs.items():
            replacement = getattr(donor, organ, default)
            setattr(patient, organ, replacement)
        return patient

    return transplantation


class pfxless:  # noqa: N801
    pattern: str | re.Pattern[str]

    def __init__(
        self,
        *,
        regex: str | re.Pattern[str] | None = None,
        re_flags: int | re.RegexFlag | None = None,
        enabled: bool = True,
        chance: Number = 1,  # percentage to trigger a response
        allow_prefix: bool = False,  # allow messages starting with bot prefix
        allow_bots: bool = False,  # allow bot message authors
        plain_text_only: bool = True,  # excludes matches inside emojis, mentions, etc.
        permission_key: str | None = None,
        guild_only: bool = False,
        variants: tuple[str, ...] = (),
        delegates_to: str | None = None,
    ):
        self.enabled = enabled
        self.chance = chance
        self.allow_prefix = allow_prefix
        self.allow_bots = allow_bots
        self.plain_text_only = plain_text_only
        self.permission_key = permission_key
        self.guild_only = guild_only
        self.variants = variants
        self.delegates_to = delegates_to

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

    def __call__[T: CogMsgListener](self, func: T) -> T:
        if self.pattern is None:
            self.pattern = rf"\b{func.__name__.replace('_', ' ')}\b"

        if self.plain_text_only:
            # For now this only checks if word containing pattern is not adjacent to a colon
            self.pattern = rf"(?<![:\w])(?:{self.pattern})(?![:\w])"  # TODO: exclude mentions too

        self.event = self.wrap_callback(func)
        return self.event

    def wrap_callback[T: CogMsgListener](self, coro: T) -> T:
        @commands.Cog.listener("on_message")
        @functools.wraps(coro)
        @copy_dpy_attrs_from(coro)
        async def wrapper(cog: commands.Cog, msg: Message) -> None:
            if not wrapper.enabled or not msg.guild:
                return
            try:
                if not await self.prepare(msg, cog.ara):
                    return
                try:
                    await coro(cog, msg)
                finally:
                    if wrapper.__commands_max_concurrency__:
                        await wrapper.__commands_max_concurrency__.release(msg)
            except commands.CheckFailure, commands.DisabledCommand:
                # Permission lookup failures are logged by the permission service.
                return

        wrapper.enabled = self.enabled
        wrapper.__pfxless__ = self
        return wrapper

    async def prepare(self, msg: Message, ara: Ara) -> bool:
        match = await self._check_message(msg, functools.partial(ara.command_prefix, ara))
        if not match:
            return False
        await ara.permissions.check_event(self, msg, match)
        if not await self._run_checks(msg) or not await self._check_concurrency(msg):
            return False
        prepared = False
        try:
            prepared = self._check_cooldown(msg) and self.chance > random.random()
            return prepared
        finally:
            if not prepared and self.event.__commands_max_concurrency__:
                await self.event.__commands_max_concurrency__.release(msg)

    async def _check_message(self, msg: Message, pfx_factory: Callable[[Message], Awaitable]) -> re.Match | bool | None:
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
