import logging
from asyncio import timeout
from contextlib import suppress
from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands
from sqlalchemy.exc import SQLAlchemyError

from arabot.core import Ara, Category, Cog
from arabot.core.permissions import PermissionConfigurationError, PermissionTarget
from arabot.utils.pagination import ButtonFlag, EmbedPaginator

if TYPE_CHECKING:
    from arabot.core.database.permissions import Override, Policy, PolicyChange

logger = logging.getLogger(__name__)


def state_name(value: bool | None) -> str:
    return "Fallthrough" if value is None else "Allow" if value else "Deny"


def target_name(guild: disnake.Guild | None, target: PermissionTarget) -> str:
    if target.kind == "guild":
        return "This server"
    if target.kind == "global":
        return "Global — all servers"
    entity = None
    if guild:
        if target.kind == "user":
            entity = guild.get_member(target.entity_id)
        elif target.kind == "role":
            entity = guild.get_role(target.entity_id)
        else:
            entity = guild.get_channel(target.entity_id)
    name = getattr(entity, "display_name", None) or getattr(entity, "name", None)
    return f"{target.kind.title()}: {name or 'deleted / unavailable'} ({target.entity_id})"


def override_line(guild: disnake.Guild, rule: Override) -> str:
    label = target_name(guild, PermissionTarget(rule.target_type, rule.target_id))
    return f"{disnake.utils.escape_markdown(label)}: **{state_name(rule.allowed)}**"


def policy_lines(guild: disnake.Guild, policy: Policy) -> list[str]:
    group = {None: "None", "members": "Users / roles", "locations": "Channels / categories"}[policy.scope_mode]
    lines = [f"Server: **{state_name(policy.guild_allowed)}** · Override group: **{group}**"]
    lines.extend(override_line(guild, rule) for rule in policy.overrides)
    return lines


def make_pages(title: str, lines: list[str]) -> list[disnake.Embed]:
    pages = []
    content = ""
    for line in lines:
        if len(content) + len(line) + 1 > 3800:
            pages.append(disnake.Embed(title=title, description=content))
            content = ""
        content += line + "\n"
    pages.append(disnake.Embed(title=title, description=content or "No entries."))
    return pages


class Permissions(Cog, category=Category.SETTINGS):
    permission_configurable = False

    def __init__(self, ara: Ara) -> None:
        self.ara = ara

    @commands.slash_command(
        name="permissions",
        description="Manage command permissions",
        default_member_permissions=disnake.Permissions(manage_guild=True),
        contexts=disnake.InteractionContextTypes(guild=True, bot_dm=True),
    )
    async def permissions(self, inter: disnake.ApplicationCommandInteraction):
        if not await self.ara.permissions.can_configure(inter):
            raise PermissionConfigurationError(
                "Manage Server is required. Global controls are reserved for the bot owner."
            )

    @permissions.sub_command(name="set", description="Set permissions for a command, category, or all misc sounds")
    async def set_permission(
        self,
        inter: disnake.ApplicationCommandInteraction,
        command: str = commands.Param(description="Command, command category, or misc_voice bulk selector"),
        state: str = commands.Param(
            choices={"Allow / Enable": "allow", "Deny / Disable": "deny", "Fallthrough": "inherit"},
            description="Allow, deny, or remove a user/role/channel/category override",
        ),
        target: str = commands.Param(
            default="guild", description="Defaults to this server; only the owner can select Global"
        ),
    ):
        if state not in {"allow", "deny", "inherit"}:
            raise PermissionConfigurationError("Invalid state.")
        parsed_target = PermissionTarget.parse(target)
        await inter.response.defer(ephemeral=True)
        allowed = {"allow": True, "deny": False, "inherit": None}[state]
        changes, skipped, global_changes = await self.ara.permissions.set_permission(
            inter, command, parsed_target, allowed
        )
        scope = "Global — all servers" if target == "global" else f"Server: {inter.guild.name}"
        lines = [
            f"**{disnake.utils.escape_markdown(scope)}**",
            f"Target: {disnake.utils.escape_markdown(target_name(inter.guild, parsed_target))}",
            f"Value: **{state_name(allowed)}**",
        ]
        if global_changes:
            for key, (before, after) in global_changes.items():
                unit = self.ara.permissions.registry.units.get(key)
                label = unit.label if unit else key
                status = "Unchanged" if before == after else "Updated"
                lines.append(
                    f"**{disnake.utils.escape_markdown(label)}** — {status}: {state_name(before)} → {state_name(after)}"
                )
        else:
            lines.extend(self.change_lines(inter.guild, changes))
        if skipped:
            if not changes:
                lines.append("No commands changed.")
            lines.append("\n**Skipped — voice events only support server/global settings**")
            lines.extend(disnake.utils.escape_markdown(unit.label) for unit in skipped)
        await self.send_result(inter, "Command permissions", lines)

    @permissions.sub_command(name="view", description="Show current command permissions")
    async def view_permissions(
        self,
        inter: disnake.ApplicationCommandInteraction,
        command: str = commands.Param(description="Command, command category, or misc_voice bulk selector"),
        scope: str = commands.Param(default="guild", description="This server, or Global for the bot owner"),
    ):
        await self.ara.permissions.authorize(inter, scope)
        await inter.response.defer(ephemeral=True)
        units = self.ara.permissions.registry.resolve(command)
        lines = [
            "**Global — all servers**"
            if scope == "global"
            else f"**Server: {disnake.utils.escape_markdown(inter.guild.name)}**"
        ]
        for unit in units:
            lines.extend(
                ("", f"**{disnake.utils.escape_markdown(unit.label)}**", f"Global: **{state_name(unit.enabled)}**")
            )
            if scope == "guild":
                lines.extend(policy_lines(inter.guild, await self.ara.permissions.policy(inter.guild.id, unit.key)))
        await self.send_result(inter, "Current command permissions", lines)

    @permissions.sub_command(
        name="reset", description="Restore server allow and remove all overrides for selected commands"
    )
    async def reset_permissions(
        self,
        inter: disnake.ApplicationCommandInteraction,
        command: str = commands.Param(description="Command, command category, or misc_voice bulk selector"),
    ):
        await self.ara.permissions.authorize(inter, "guild")
        await inter.response.defer(ephemeral=True)
        changes = await self.ara.permissions.reset(inter, command)
        lines = [f"**Server: {disnake.utils.escape_markdown(inter.guild.name)}**", "Restored server defaults."]
        lines.extend(self.change_lines(inter.guild, changes))
        await self.send_result(inter, "Command permissions reset", lines)

    def change_lines(self, guild: disnake.Guild, changes: list[PolicyChange]) -> list[str]:
        lines = []
        for change in changes:
            unit = self.ara.permissions.registry.units.get(change.command_key)
            label = unit.label if unit else change.command_key
            status = "Unchanged" if change.before == change.after else "Updated"
            enabled = (
                unit.enabled if unit else self.ara.permissions.registry.global_settings.get(change.command_key, True)
            )
            lines.extend(
                ("", f"**{disnake.utils.escape_markdown(label)}** — {status}", f"Global: **{state_name(enabled)}**")
            )
            lines.extend(policy_lines(guild, change.after))
            remaining = {(rule.target_type, rule.target_id) for rule in change.after.overrides}
            removed = [rule for rule in change.before.overrides if (rule.target_type, rule.target_id) not in remaining]
            if removed:
                lines.append("Removed overrides:")
                lines.extend(override_line(guild, rule) for rule in removed)
        return lines

    @staticmethod
    async def send_result(inter: disnake.ApplicationCommandInteraction, title: str, lines: list[str]) -> None:
        pages = make_pages(title, lines)
        view = EmbedPaginator(
            pages,
            author=inter.author,
            buttons=ButtonFlag.PREV | ButtonFlag.NEXT,
            shared_buttons=ButtonFlag(0),
        )
        # Complete the private defer before sending a separate public follow-up.
        await inter.edit_original_response(content="Done.")
        await inter.followup.send(embed=pages[0], view=view, ephemeral=False)
        with suppress(disnake.HTTPException):
            await inter.delete_original_response()

    @set_permission.autocomplete("command")
    @view_permissions.autocomplete("command")
    @reset_permissions.autocomplete("command")
    async def command_autocomplete(self, inter: disnake.ApplicationCommandInteraction, query: str):
        if not await self.ara.permissions.can_configure(inter):
            return []
        chain, options = inter.data._get_chain_and_kwargs()
        scope = None
        if chain == ("reset",):
            scope = "guild"
        elif "scope" in options:
            scope = options["scope"]
        elif "target" in options:
            scope = "global" if options["target"] == "global" else "guild"
        if scope:
            try:
                await self.ara.permissions.authorize(inter, scope)
            except PermissionConfigurationError:
                return []
        return self.ara.permissions.registry.choices(query)

    @view_permissions.autocomplete("scope")
    async def scope_autocomplete(self, inter: disnake.ApplicationCommandInteraction, query: str):
        candidates = []
        if inter.guild and inter.author.guild_permissions.manage_guild:
            candidates.append(disnake.OptionChoice(name="This server", value="guild"))
        if await self.ara.is_owner(inter.author):
            candidates.append(disnake.OptionChoice(name="Global — all servers", value="global"))
        return [choice for choice in candidates if query.casefold() in f"{choice.name} {choice.value}".casefold()]

    @set_permission.autocomplete("target")
    async def target_autocomplete(self, inter: disnake.ApplicationCommandInteraction, query: str):
        candidates = await self.scope_autocomplete(inter, "")
        if not inter.guild or not inter.author.guild_permissions.manage_guild:
            return [choice for choice in candidates if query.casefold() in f"{choice.name} {choice.value}".casefold()]
        units = []
        selector = inter.filled_options.get("command")
        if selector:
            try:
                units = self.ara.permissions.registry.resolve(selector)
            except PermissionConfigurationError:
                return []
            if all(unit.guild_only for unit in units):
                return [
                    choice for choice in candidates if query.casefold() in f"{choice.name} {choice.value}".casefold()
                ]

        entities = [
            *(("user", member) for member in inter.guild.members),
            *(("role", role) for role in inter.guild.roles if not role.is_default()),
            *(
                ("category" if isinstance(channel, disnake.CategoryChannel) else "channel", channel)
                for channel in inter.guild.channels
            ),
        ]
        targets = {}
        search = query.casefold().strip()
        for kind, entity in entities:
            name = getattr(entity, "display_name", entity.name)
            label = f"{kind.title()}: {name} ({entity.id})"
            if search in f"{label} {entity.name} {entity.mention}".casefold():
                targets[f"{kind}:{entity.id}"] = disnake.OptionChoice(name=label[:100], value=f"{kind}:{entity.id}")
        # Stored targets are only valid without a live guild entity when removing an override.
        if units and inter.filled_options.get("state") == "inherit":
            try:
                async with timeout(1.5):
                    stored = await self.ara.permissions.stored_targets(inter.guild.id, [unit.key for unit in units])
                for target in stored:
                    if target.kind == "role" and target.entity_id == inter.guild.id:
                        continue
                    label = target_name(inter.guild, target)
                    if search in label.casefold():
                        targets[target.value] = disnake.OptionChoice(name=label[:100], value=target.value)
            except TimeoutError, SQLAlchemyError:
                logger.warning("Could not load stored permission targets for autocomplete")
        filtered = [choice for choice in candidates if search in f"{choice.name} {choice.value}".casefold()]
        filtered.extend(sorted(targets.values(), key=lambda choice: choice.name.casefold()))
        return filtered[:25]


def setup(ara: Ara):
    ara.add_cog(Permissions(ara))
