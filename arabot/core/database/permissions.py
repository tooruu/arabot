from asyncio import Lock
from collections import OrderedDict
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Text, UniqueConstraint, delete, select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from arabot.core.database.base import Model, UnsignedInt64
from arabot.core.database.engine import get_session

type TargetType = Literal["user", "role", "channel", "category"]
type ScopeMode = Literal["members", "locations"]


class CommandGlobalSetting(Model):
    __tablename__ = "command_global_settings"

    command_key: Mapped[str] = mapped_column(Text, primary_key=True)
    enabled: Mapped[bool] = mapped_column(nullable=False)


class GuildCommandPermission(Model):
    __tablename__ = "guild_command_permissions"
    __table_args__ = (
        UniqueConstraint("guild_id", "command_key", "scope_mode"),
        CheckConstraint("scope_mode IN ('members', 'locations')", name="valid_permission_scope"),
    )

    guild_id: Mapped[int] = mapped_column(UnsignedInt64, primary_key=True)
    command_key: Mapped[str] = mapped_column(Text, primary_key=True)
    guild_allowed: Mapped[bool] = mapped_column(default=True, server_default=true())
    scope_mode: Mapped[str | None] = mapped_column(Text, default=None)


class CommandPermissionOverride(Model):
    __tablename__ = "command_permission_overrides"
    __table_args__ = (
        ForeignKeyConstraint(
            ["guild_id", "command_key", "scope_mode"],
            [
                "guild_command_permissions.guild_id",
                "guild_command_permissions.command_key",
                "guild_command_permissions.scope_mode",
            ],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "(scope_mode = 'members' AND target_type IN ('user', 'role')) OR "
            "(scope_mode = 'locations' AND target_type IN ('channel', 'category'))",
            name="matching_permission_target_scope",
        ),
        CheckConstraint("target_type <> 'role' OR target_id <> guild_id", name="no_everyone_override"),
    )

    guild_id: Mapped[int] = mapped_column(UnsignedInt64, primary_key=True)
    command_key: Mapped[str] = mapped_column(Text, primary_key=True)
    target_type: Mapped[str] = mapped_column(Text, primary_key=True)
    target_id: Mapped[int] = mapped_column(UnsignedInt64, primary_key=True)
    scope_mode: Mapped[str] = mapped_column(Text)
    allowed: Mapped[bool]


@dataclass(frozen=True)
class Override:
    target_type: TargetType
    target_id: int
    allowed: bool


@dataclass(frozen=True)
class Policy:
    guild_allowed: bool = True
    scope_mode: ScopeMode | None = None
    overrides: tuple[Override, ...] = ()

    def value(self, target_type: TargetType, target_id: int) -> bool | None:
        return next(
            (rule.allowed for rule in self.overrides if (rule.target_type, rule.target_id) == (target_type, target_id)),
            None,
        )


@dataclass(frozen=True)
class PolicyChange:
    command_key: str
    before: Policy
    after: Policy


class PermissionRepository:
    """Single-process policy cache; striped locks also bound synchronization memory."""

    CACHE_SIZE = 2048

    def __init__(self) -> None:
        self._cache: OrderedDict[tuple[int, str], Policy] = OrderedDict()
        self._locks = [Lock() for _ in range(64)]

    def _stripe(self, guild_id: int, key: str) -> int:
        return hash((guild_id, key)) % len(self._locks)

    def _cache_policy(self, guild_id: int, key: str, policy: Policy) -> None:
        cache_key = (guild_id, key)
        self._cache[cache_key] = policy
        self._cache.move_to_end(cache_key)
        while len(self._cache) > self.CACHE_SIZE:
            self._cache.popitem(last=False)

    async def get(self, guild_id: int, key: str) -> Policy:
        async with self._locks[self._stripe(guild_id, key)]:
            cache_key = (guild_id, key)
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                return self._cache[cache_key]
            async with get_session() as session:
                # One statement gives the fallback and overrides the same database snapshot.
                rows = (
                    await session.execute(
                        select(GuildCommandPermission, CommandPermissionOverride)
                        .outerjoin(CommandPermissionOverride)
                        .where(GuildCommandPermission.guild_id == guild_id, GuildCommandPermission.command_key == key)
                        .order_by(CommandPermissionOverride.target_type, CommandPermissionOverride.target_id)
                    )
                ).all()
                policy = (
                    Policy(
                        rows[0][0].guild_allowed,
                        rows[0][0].scope_mode,
                        tuple(Override(row.target_type, row.target_id, row.allowed) for _, row in rows if row),
                    )
                    if rows
                    else Policy()
                )
            self._cache_policy(guild_id, key, policy)
            return policy

    async def edit(
        self,
        guild_id: int,
        keys: list[str],
        target_type: str | None,
        target_id: int | None,
        allowed: bool | None,
    ) -> list[PolicyChange]:
        """Reset policies for a None target, or remove an override for a None value."""
        keys = sorted(set(keys))
        changes = []
        async with AsyncExitStack() as stack:
            for stripe in sorted({self._stripe(guild_id, key) for key in keys}):
                await stack.enter_async_context(self._locks[stripe])
            async with get_session() as session:
                for key in keys:
                    await session.execute(
                        insert(GuildCommandPermission)
                        .values(guild_id=guild_id, command_key=key)
                        .on_conflict_do_nothing()
                    )
                    parent = await session.scalar(
                        select(GuildCommandPermission)
                        .where(GuildCommandPermission.guild_id == guild_id, GuildCommandPermission.command_key == key)
                        .with_for_update()
                    )
                    rule_filter = (
                        CommandPermissionOverride.guild_id == guild_id,
                        CommandPermissionOverride.command_key == key,
                    )
                    rows = (await session.scalars(select(CommandPermissionOverride).where(*rule_filter))).all()
                    old_rules = tuple(
                        sorted(
                            (Override(row.target_type, row.target_id, row.allowed) for row in rows),
                            key=lambda row: (row.target_type, row.target_id),
                        )
                    )
                    before = Policy(parent.guild_allowed, parent.scope_mode, old_rules)
                    rules = {(rule.target_type, rule.target_id): rule.allowed for rule in old_rules}

                    if target_type is None:
                        await session.delete(parent)
                        after = Policy()
                    elif target_type == "guild":
                        parent.guild_allowed = allowed
                        after = Policy(allowed, parent.scope_mode, old_rules)
                    else:
                        mode = "members" if target_type in {"user", "role"} else "locations"
                        if allowed is not None and parent.scope_mode != mode:
                            rules.clear()
                        if allowed is None:
                            rules.pop((target_type, target_id), None)
                        else:
                            rules[target_type, target_id] = allowed
                        # Delete children before changing the mode referenced by their foreign key.
                        await session.execute(delete(CommandPermissionOverride).where(*rule_filter))
                        parent.scope_mode = (mode if allowed is not None else parent.scope_mode) if rules else None
                        await session.flush()
                        for (kind, entity_id), value in sorted(rules.items()):
                            session.add(
                                CommandPermissionOverride(
                                    guild_id=guild_id,
                                    command_key=key,
                                    target_type=kind,
                                    target_id=entity_id,
                                    scope_mode=parent.scope_mode,
                                    allowed=value,
                                )
                            )
                        after = Policy(
                            parent.guild_allowed,
                            parent.scope_mode,
                            tuple(
                                Override(kind, entity_id, value) for (kind, entity_id), value in sorted(rules.items())
                            ),
                        )
                    await session.flush()
                    changes.append(PolicyChange(key, before, after))
            # Commit succeeded. Readers share these locks and cannot publish an older snapshot.
            for change in changes:
                self._cache_policy(guild_id, change.command_key, change.after)
        return changes
