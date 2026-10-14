import re
from contextlib import suppress
from typing import TYPE_CHECKING, Any

import disnake
from disnake.ext import commands

from arabot.core.permissions import PermissionConfigurationError

if TYPE_CHECKING:
    from arabot.core.patches import Context


async def manage_server_or_owner(ctx: Context) -> bool:
    if await ctx.ara.is_owner(ctx.author) or (ctx.guild and ctx.author.guild_permissions.manage_guild):
        return True
    raise PermissionConfigurationError("Manage Server is required.")


def entity_id(argument: str) -> int | None:
    match = re.fullmatch(r"(?:<[@#](?:[!&])?)?(\d{1,20})>?", argument)
    return int(match[1]) if match and 0 < int(match[1]) < 1 << 64 else None


async def resolve_member_bucket(ctx: Context, kind: commands.BucketType, argument: str | None, owner: bool):
    guild = ctx.guild
    # Owners can explicitly address a member bucket in another guild.
    if argument and "/" in argument:
        guild_text, argument = argument.split("/", 1)
        if not owner or not guild_text.isdecimal() or not (guild := ctx.ara.get_guild(int(guild_text))):
            raise PermissionConfigurationError("Invalid guild/member target.")
    member_id = entity_id(argument) if argument else ctx.author.id
    member = guild.get_member(member_id) if guild and member_id else None
    if argument and member_id is None and guild:
        matches = [m for m in guild.members if argument.casefold() in {m.name.casefold(), m.display_name.casefold()}]
        if len(matches) == 1:
            member = matches[0]
            member_id = member.id
    if kind is commands.BucketType.user:
        if member_id is None:
            raise PermissionConfigurationError("User not found. Supply a user ID or mention.")
        return member_id, f"user {member_id} across all servers"
    if guild is None:
        raise PermissionConfigurationError("A member cooldown needs a guild. Owners may use guild_id/user_id.")
    if member is None and member_id:
        with suppress(disnake.NotFound):
            member = await guild.fetch_member(member_id)
    if member is None or (not owner and member.guild.id != ctx.guild.id):
        raise PermissionConfigurationError("Member not found in the permitted guild.")
    return (guild.id, member.id), f"member {member.id} in server {guild.id}"


async def resolve_bucket_target(ctx: Context, kind: commands.BucketType, argument: str | None, owner: bool):
    guild = ctx.guild
    if kind is commands.BucketType.default:
        if argument:
            raise PermissionConfigurationError("A global cooldown does not accept a bucket target.")
        return None, "all users and servers"
    if kind in {commands.BucketType.member, commands.BucketType.user}:
        return await resolve_member_bucket(ctx, kind, argument, owner)

    guilds = ctx.ara.guilds if owner else [guild] if guild else []
    if kind is commands.BucketType.guild:
        candidates = guilds
        default = guild
    elif kind is commands.BucketType.role:
        candidates = [role for server in guilds for role in server.roles]
        default = getattr(ctx.author, "top_role", None)
    elif kind is commands.BucketType.category:
        candidates = [category for server in guilds for category in server.categories]
        default = getattr(ctx.channel, "category", None) or ctx.channel
    else:
        candidates = [
            channel
            for server in guilds
            for channel in [*server.channels, *server.threads]
            if not isinstance(channel, disnake.CategoryChannel)
        ]
        default = ctx.channel
    if argument:
        target_id = entity_id(argument)
        matches = [
            obj
            for obj in candidates
            if obj.id == target_id or (target_id is None and obj.name.casefold() == argument.casefold())
        ]
        if len(matches) != 1:
            raise PermissionConfigurationError(
                "Bucket target is missing, ambiguous, or outside your server. Use its ID."
            )
        target = matches[0]
    else:
        target = default
    if target is None:
        raise PermissionConfigurationError("Supply a target for this cooldown bucket.")
    target_guild = target if isinstance(target, disnake.Guild) else getattr(target, "guild", None)
    if not owner and (target_guild is None or target_guild.id != ctx.guild.id):
        raise PermissionConfigurationError("You can only reset cooldowns inside your server.")
    return target.id, f"{kind.name} {target.id}"


async def reset_unit_cooldowns(ctx: Context, selector: str, argument: str | None) -> list[str]:
    units = ctx.ara.permissions.registry.resolve(selector)
    if len(units) != 1:
        raise PermissionConfigurationError("Select one command, not a category or sound group.")
    unit = units[0]
    if unit.kind in {"event", "sound"}:
        raise PermissionConfigurationError("Pfxless cooldowns cannot be reset, including by the bot owner.")
    owner = await ctx.ara.is_owner(ctx.author)
    if not owner and (not ctx.guild or not ctx.author.guild_permissions.manage_guild):
        raise PermissionConfigurationError("Manage Server is required.")

    pending: list[tuple[str, commands.CooldownMapping, Any, str]] = []
    lines = []
    for implementation in unit.implementations:
        form = "prefix" if isinstance(implementation, commands.Command) else "slash"
        label = f"{implementation.qualified_name} [{form}]"
        mapping = implementation._buckets
        if not mapping.valid:
            lines.append(f"{label}: no cooldown")
            continue
        kind = mapping.type
        if not isinstance(kind, commands.BucketType):
            raise PermissionConfigurationError("Custom cooldown bucket mappings cannot be reset.")
        if not owner and kind in {commands.BucketType.default, commands.BucketType.user}:
            raise PermissionConfigurationError(
                "This command has a cooldown shared across servers. Only the bot owner can reset it."
            )
        key, target = await resolve_bucket_target(ctx, kind, argument, owner)
        pending.append((label, mapping, key, target))

    # All forms and target scopes are validated before touching any cooldown state.
    for label, mapping, key, target in pending:
        bucket = mapping._cooldown if mapping._is_default() else mapping._cache.get(key)
        if bucket is None or bucket.get_tokens() == bucket.rate:
            lines.append(f"{label}: no active cooldown for {target}")
        else:
            bucket.reset()
            lines.append(f"{label}: cooldown reset for {target}")
    return lines
