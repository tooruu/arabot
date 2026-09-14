import logging
import re
from asyncio import Lock
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import disnake
from disnake.ext import commands
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from arabot.core.database.engine import get_session
from arabot.core.database.permissions import (
    CommandGlobalSetting,
    CommandPermissionOverride,
    PermissionRepository,
    Policy,
    PolicyChange,
)
from arabot.core.enums import Category

if TYPE_CHECKING:
    from collections.abc import Callable

    from arabot.core.bot import Ara
    from arabot.core.patches import Context
    from arabot.core.pfxless import pfxless

type Implementation = commands.Command | commands.InvokableApplicationCommand
type Origin = commands.Context | disnake.ApplicationCommandInteraction | disnake.Message

logger = logging.getLogger(__name__)


class PermissionDenied(commands.CheckFailure):
    pass


class PermissionUnavailable(commands.CheckFailure):
    pass


class PermissionConfigurationError(commands.CommandError):
    pass


@dataclass
class CommandUnit:
    key: str
    name: str
    category: Category
    kind: str
    enabled: bool = True
    guild_only: bool = False
    aliases: set[str] = field(default_factory=set)
    implementations: list[Implementation] = field(default_factory=list)
    event: Callable | None = None

    @property
    def label(self) -> str:
        forms = "/ + prefix" if len(self.implementations) > 1 else self.kind
        return f"{self.name} [{forms}]"

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        for implementation in self.implementations:
            implementation.enabled = enabled
        if self.event is not None:
            self.event.enabled = enabled


class CommandRegistry:
    def __init__(self, ara: Ara) -> None:
        self.ara = ara
        self.units: dict[str, CommandUnit] = {}
        self.global_settings: dict[str, bool] = {}
        self._implementation_keys: dict[Implementation, str] = {}
        self._event_keys: dict[Callable, str] = {}
        self._bulk: dict[str, tuple[str, list[str]]] = {}

    @staticmethod
    def protected(command: Implementation) -> bool:
        cog = command.cog or getattr(getattr(command, "root_parent", None), "cog", None)
        return not getattr(cog, "permission_configurable", True) or command.extras.get("permission_protected", False)

    @staticmethod
    def category_for(command: Implementation) -> Category:
        cog = command.cog or getattr(getattr(command, "root_parent", None), "cog", None)
        return command.extras.get("category") or getattr(cog, "category", Category.NO_CATEGORY)

    def refresh(self) -> None:
        """Read live registrations, including subcommands added directly to existing groups."""
        units, implementation_keys, event_keys, bulk = {}, {}, {}, {}

        def register(command: Implementation, kind: str) -> None:
            if self.protected(command):
                return
            key = command.extras.get("permission_key", f"{kind}:{command.qualified_name}")
            category = self.category_for(command)
            if key not in units:
                units[key] = CommandUnit(key, command.qualified_name, category, kind)
            unit = units[key]
            unit.enabled = unit.enabled and getattr(command, "enabled", True)
            unit.implementations.append(command)
            unit.aliases.update((key, command.qualified_name, command.name))
            for alias in getattr(command, "aliases", ()):
                unit.aliases.add(f"{command.full_parent_name} {alias}".strip())
            implementation_keys[command] = key

        for command in self.ara.walk_commands():
            register(command, "prefix")

        def register_slash(command: Implementation) -> None:
            children = getattr(command, "children", {})
            if children:
                for child in children.values():
                    register_slash(child)
            else:
                register(command, "slash")

        for command in self.ara.slash_commands:
            register_slash(command)
        for cog in self.ara.cogs.values():
            if not getattr(cog, "permission_configurable", True):
                continue
            for _, listener in cog.get_listeners():
                event = listener.__func__
                metadata = getattr(event, "__pfxless__", None)
                if metadata is None:
                    continue
                key = metadata.permission_key or f"event:{cog.qualified_name}.{event.__name__}"
                event_keys[event] = key
                category = getattr(cog, "category", Category.NO_CATEGORY)
                if metadata.variants:
                    keys = []
                    for name in metadata.variants:
                        sound_key = f"{key}/{name}"
                        units[sound_key] = CommandUnit(
                            sound_key, name, category, "sound", metadata.enabled, True, {name, sound_key}
                        )
                        keys.append(sound_key)
                    bulk[key] = (event.__name__, keys)
                else:
                    units[key] = CommandUnit(
                        key,
                        event.__name__,
                        category,
                        "event",
                        getattr(event, "enabled", metadata.enabled),
                        metadata.guild_only,
                        {key, event.__name__},
                        event=event,
                    )

        for key, unit in units.items():
            if len(key) > 100:
                raise ValueError(f"Permission key exceeds Discord's option value limit: {key}")
            unit.set_enabled(self.global_settings.get(key, unit.enabled))
        for event, key in event_keys.items():
            if key in bulk:
                event.enabled = any(units[sound_key].enabled for sound_key in bulk[key][1])
        self.units = units
        self._implementation_keys = implementation_keys
        self._event_keys = event_keys
        self._bulk = bulk

    def for_command(self, command: Implementation) -> CommandUnit | None:
        if command is None or self.protected(command):
            return None
        if command not in self._implementation_keys:
            self.refresh()
        key = self._implementation_keys.get(command)
        if key is None:
            kind = "prefix" if isinstance(command, commands.Command) else "slash"
            key = command.extras.get("permission_key", f"{kind}:{command.qualified_name}")
        return self.units.get(key)

    def for_event(self, event: Callable, variant: str | None = None) -> CommandUnit:
        if event not in self._event_keys:
            self.refresh()
        key = self._event_keys.get(event)
        if variant is not None:
            key = f"{key}/{variant}"
        if key not in self.units:
            logger.error("Pfxless permission unit is not registered: %s", key)
            raise PermissionUnavailable
        return self.units[key]

    def resolve(self, selector: str) -> list[CommandUnit]:
        self.refresh()
        if selector in self.units:
            return [self.units[selector]]
        if selector in self._bulk:
            return [self.units[key] for key in self._bulk[selector][1]]
        if selector.startswith("category:"):
            category = selector.removeprefix("category:")
            found = [unit for unit in self.units.values() if unit.category.name == category]
            if found:
                return sorted(found, key=lambda unit: unit.key)
        matches = [unit for unit in self.units.values() if selector.casefold() in {a.casefold() for a in unit.aliases}]
        for name, keys in self._bulk.values():
            if selector.casefold() == name.casefold():
                return [self.units[key] for key in keys]
        if len(matches) == 1:
            return matches
        raise PermissionConfigurationError("Unknown or ambiguous command. Select a command from autocomplete.")

    def is_bulk(self, selector: str) -> bool:
        return (
            selector.startswith("category:")
            or selector in self._bulk
            or any(selector.casefold() == name.casefold() for name, _ in self._bulk.values())
        )

    def choices(self, query: str) -> list[disnake.OptionChoice]:
        self.refresh()
        candidates = []
        for unit in self.units.values():
            terms = " ".join((*unit.aliases, unit.category.value, unit.kind))
            candidates.append((unit.label, unit.key, terms))
        candidates.extend(
            (f"Category: {category.value}", f"category:{category.name}", category.value)
            for category in {unit.category for unit in self.units.values()}
        )
        for key, (name, _) in self._bulk.items():
            candidates.append((f"{name} [all current sounds]", key, name))
        query = query.casefold()
        matches = [item for item in candidates if query in f"{item[0]} {item[2]}".casefold()]
        matches.sort(key=lambda item: (not item[0].casefold().startswith(query), item[0].casefold()))
        return [disnake.OptionChoice(name=label[:100], value=key) for label, key, _ in matches[:25]]


@dataclass(frozen=True)
class PermissionTarget:
    kind: str
    entity_id: int | None = None

    @classmethod
    def parse(cls, value: str) -> PermissionTarget:
        if value in {"guild", "global"}:
            return cls(value)
        match = re.fullmatch(r"(user|role|channel|category):(\d{1,20})", value)
        if not match or not 0 < int(match[2]) < 1 << 64:
            raise PermissionConfigurationError("Invalid target. Select a target from autocomplete.")
        return cls(match[1], int(match[2]))

    @property
    def value(self) -> str:
        return f"{self.kind}:{self.entity_id}" if self.entity_id is not None else self.kind


class PermissionService:
    def __init__(self, ara: Ara) -> None:
        self.ara = ara
        self.registry = CommandRegistry(ara)
        self.repository = PermissionRepository()
        self._global_lock = Lock()
        self.ready = False

    async def initialize(self) -> None:
        async with get_session() as session:
            rows = (await session.execute(select(CommandGlobalSetting.command_key, CommandGlobalSetting.enabled))).all()
        self.registry.global_settings = dict(rows)
        self.registry.refresh()
        self.ready = True

    async def policy(self, guild_id: int, key: str) -> Policy:
        if not self.ready:
            raise PermissionUnavailable
        try:
            return await self.repository.get(guild_id, key)
        except SQLAlchemyError as exc:
            logger.exception("Could not read command permissions")
            raise PermissionUnavailable from exc

    async def check(self, unit: CommandUnit, origin: Origin) -> None:
        if not unit.enabled or any(not impl.enabled for impl in unit.implementations):
            raise commands.DisabledCommand
        if not origin.guild:
            return
        if isinstance(origin.author, disnake.Member) and origin.author.guild_permissions.manage_guild:
            return
        if any(impl.extras.get("permission_owner_bypass") for impl in unit.implementations) and await self.ara.is_owner(
            origin.author
        ):
            return
        policy = await self.policy(origin.guild.id, unit.key)
        allowed = None
        if not unit.guild_only and policy.scope_mode == "members":
            allowed = policy.value("user", origin.author.id)
            if allowed is None:
                role_values = [
                    policy.value("role", role.id)
                    for role in getattr(origin.author, "roles", ())
                    if role.id != origin.guild.id
                ]
                if False in role_values:
                    allowed = False
                elif True in role_values:
                    allowed = True
        elif not unit.guild_only and policy.scope_mode == "locations":
            channel = origin.channel.parent if isinstance(origin.channel, disnake.Thread) else origin.channel
            if channel is None or not hasattr(channel, "category_id"):
                logger.warning("Cannot resolve the permission channel in guild %s", origin.guild.id)
                raise PermissionUnavailable
            allowed = policy.value("channel", channel.id)
            if allowed is None and channel.category_id is not None:
                allowed = policy.value("category", channel.category_id)
        if not (policy.guild_allowed if allowed is None else allowed):
            raise PermissionDenied

    async def prefix_check(self, ctx: Context) -> bool:
        command = ctx.command
        leaf = getattr(ctx, "permission_command", None)
        if leaf is not None and command in [leaf, *leaf.parents]:
            command = leaf
        if unit := self.registry.for_command(command):
            await self.check(unit, ctx)
        return True

    async def slash_check(self, inter: disnake.ApplicationCommandInteraction) -> bool:
        command = self.ara.get_slash_command(inter.data.name)
        chain, _ = inter.data._get_chain_and_kwargs()
        for name in chain:
            command = getattr(command, "children", {}).get(name)
        if command is None:
            raise PermissionConfigurationError("This command is no longer available. Refresh the slash command list.")
        if unit := self.registry.for_command(command):
            await self.check(unit, inter)
        return True

    async def check_event(self, metadata: pfxless, msg: disnake.Message, match: re.Match) -> None:
        variant = match[0].casefold() if metadata.variants else None
        await self.check(self.registry.for_event(metadata.event, variant), msg)
        if metadata.delegates_to:
            command = self.ara.get_command(metadata.delegates_to)
            if command is None:
                logger.error("Pfxless command dependency is not registered: %s", metadata.delegates_to)
                raise PermissionUnavailable
            ctx = await self.ara.get_context(msg)
            ctx.command = command
            if not await command.can_run(ctx):
                raise PermissionDenied

    async def invoke_from_event(self, msg: disnake.Message, command: commands.Command, **kwargs: Any) -> None:
        """Call with already parsed arguments, retaining all command checks and silent denials."""
        ctx = await self.ara.get_context(msg)
        ctx.command = command
        try:
            await self.invoke_command(ctx, command, **kwargs)
        except commands.CheckFailure, commands.DisabledCommand:
            return

    @staticmethod
    async def invoke_command(ctx: Context, command: commands.Command, **kwargs: Any) -> None:
        original_command = ctx.command
        original_leaf = getattr(ctx, "permission_command", None)
        ctx.command = ctx.permission_command = command
        try:
            if not await command.can_run(ctx):
                raise PermissionDenied
            await command(ctx, **kwargs)
        finally:
            ctx.command = original_command
            ctx.permission_command = original_leaf

    async def authorize(self, inter: disnake.ApplicationCommandInteraction, scope: str) -> None:
        if scope == "global":
            if not await self.ara.is_owner(inter.author):
                raise PermissionConfigurationError("Only the bot owner can change or inspect global settings.")
        elif scope == "guild":
            if not inter.guild:
                raise PermissionConfigurationError(
                    "Use this in a server, or explicitly select Global for owner controls."
                )
            if not inter.author.guild_permissions.manage_guild:
                raise PermissionConfigurationError("Manage Server is required.")
        else:
            raise PermissionConfigurationError("Invalid permission scope.")

    async def can_configure(self, inter: disnake.ApplicationCommandInteraction) -> bool:
        return bool(inter.guild and inter.author.guild_permissions.manage_guild) or await self.ara.is_owner(
            inter.author
        )

    async def stored_targets(self, guild_id: int, keys: list[str]) -> list[PermissionTarget]:
        async with get_session() as session:
            rows = (
                await session.execute(
                    select(CommandPermissionOverride.target_type, CommandPermissionOverride.target_id)
                    .where(
                        CommandPermissionOverride.guild_id == guild_id,
                        CommandPermissionOverride.command_key.in_(keys),
                    )
                    .distinct()
                )
            ).all()
        return [PermissionTarget(kind, entity_id) for kind, entity_id in rows]

    async def validate_target(
        self,
        inter: disnake.ApplicationCommandInteraction,
        target: PermissionTarget,
        units: list[CommandUnit],
        *,
        clearing: bool,
    ) -> None:
        PermissionTarget.parse(target.value)
        await self.authorize(inter, "global" if target.kind == "global" else "guild")
        if target.kind in {"guild", "global"}:
            return
        guild = inter.guild
        if target.kind == "role" and target.entity_id == guild.id:
            raise PermissionConfigurationError("@everyone is not a role target. Use This server instead.")
        entity = None
        if target.kind == "user":
            entity = guild.get_member(target.entity_id)
            if entity is None:
                with suppress(disnake.NotFound):
                    entity = await guild.fetch_member(target.entity_id)
        elif target.kind == "role":
            entity = guild.get_role(target.entity_id)
        else:
            entity = guild.get_channel(target.entity_id)
            if entity is not None:
                is_category = isinstance(entity, disnake.CategoryChannel)
                if (target.kind == "category") != is_category:
                    raise PermissionConfigurationError("The selected channel has the wrong target type.")
        if entity is not None:
            return
        if clearing:
            for unit in units:
                policy = await self.policy(guild.id, unit.key)
                if policy.value(target.kind, target.entity_id) is not None:
                    return
        raise PermissionConfigurationError("Target not found in this server. Threads use their parent channel.")

    async def set_permission(
        self,
        inter: disnake.ApplicationCommandInteraction,
        selector: str,
        target: PermissionTarget,
        allowed: bool | None,
    ) -> tuple[list[PolicyChange], list[CommandUnit], dict[str, tuple[bool, bool]]]:
        units = self.registry.resolve(selector)
        await self.validate_target(inter, target, units, clearing=allowed is None)
        if target.kind in {"guild", "global"} and allowed is None:
            raise PermissionConfigurationError("Global and server settings accept only Allow or Deny.")
        skipped = [unit for unit in units if unit.guild_only and target.kind not in {"guild", "global"}]
        eligible = [unit for unit in units if unit not in skipped]
        if not eligible:
            if self.registry.is_bulk(selector):
                return [], skipped, {}
            raise PermissionConfigurationError("Voice events only support This server or Global settings.")
        try:
            if target.kind == "global":
                async with self._global_lock:
                    self.registry.refresh()
                    global_changes = {
                        unit.key: (self.registry.global_settings.get(unit.key, unit.enabled), allowed)
                        for unit in eligible
                    }
                    async with get_session() as session:
                        for key in sorted(global_changes):
                            stmt = insert(CommandGlobalSetting).values(command_key=key, enabled=allowed)
                            await session.execute(
                                stmt.on_conflict_do_update(index_elements=["command_key"], set_={"enabled": allowed})
                            )
                    self.registry.global_settings.update(dict.fromkeys(global_changes, allowed))
                    self.registry.refresh()
                return [], [], global_changes
            changes = await self.repository.edit(
                inter.guild.id, [unit.key for unit in eligible], target.kind, target.entity_id, allowed
            )
        except SQLAlchemyError as exc:
            logger.exception("Could not update command permissions")
            raise PermissionUnavailable from exc
        return changes, skipped, {}

    async def reset(self, inter: disnake.ApplicationCommandInteraction, selector: str) -> list[PolicyChange]:
        await self.authorize(inter, "guild")
        units = self.registry.resolve(selector)
        try:
            return await self.repository.edit(inter.guild.id, [unit.key for unit in units], None, None, None)
        except SQLAlchemyError as exc:
            logger.exception("Could not reset command permissions")
            raise PermissionUnavailable from exc
