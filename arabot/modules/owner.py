import logging
from collections import defaultdict
from collections.abc import Callable, Iterable
from os import PathLike
from pathlib import Path
from typing import Any

import disnake
from disnake.abc import PrivateChannel
from disnake.ext import commands

from arabot.core import Ara, Cog, Color, Context
from arabot.utils import CIMember, CIRole, CITextChl, Empty, mono


class FakeObj:
    def __init__(self, **kwargs) -> None:
        self.__dict__ = kwargs


class CommandAlreadyEnabled(commands.CommandError):
    pass


class OwnerCommands(Cog, command_attrs=dict(hidden=True)):
    async def cog_check(self, ctx: Context):
        return await ctx.ara.is_owner(ctx.author)

    @commands.command(usage="[activity]")
    async def presence(self, ctx: Context, act_type: str = "", *, act_name: str = ""):
        acts = {
            "playing": disnake.ActivityType.playing,
            "listening": disnake.ActivityType.listening,
            "watching": disnake.ActivityType.watching,
            "competing": disnake.ActivityType.competing,
        }

        if act_type and act_type not in acts:
            await ctx.send_("invalid_presence")
            return

        if act_type and not act_name:
            await ctx.send_("no_activity")
            return

        act = disnake.Activity(type=acts[act_type], name=act_name) if act_type else None
        await ctx.ara.change_presence(activity=act)
        await ctx.tick()

    @commands.command(usage="<command> [bucket item]")
    async def resetcd(
        self,
        ctx: Context,
        input_cmd: str,
        *,
        bucket_item: disnake.TextChannel
        | CITextChl
        | disnake.Member
        | CIMember
        | disnake.Guild
        | disnake.Role
        | CIRole
        | disnake.CategoryChannel
        | Empty = False,
    ):
        if not (command := ctx.ara.get_command(input_cmd)):
            await ctx.send(ctx._("command_not_found").format(mono(input_cmd)))
            return
        buckets = command._buckets
        if not buckets.valid:
            await ctx.send(ctx._("command_no_cooldown").format(mono(str(command))))
            return
        if not isinstance(buckets.type, commands.BucketType):
            await ctx.send(ctx._("invalid_bucket_type").format(buckets.type.__name__))
            return
        if bucket_item is None:
            argument = ctx.argument_only.removeprefix(input_cmd + " ")
            await ctx.send(ctx._("bucket_item_not_found").format(mono(argument)))
            return
        if (
            bucket_item
            and buckets.type.name.lower() not in type(bucket_item).__name__.lower()
            and not (
                buckets.type is commands.BucketType.user and isinstance(bucket_item, disnake.Member)
            )
        ):
            await ctx.send(
                ctx._("bucket_doesnt_match_argument").format(
                    buckets.type.name, type(bucket_item).__name__
                )
            )
            return

        fake_msg = FakeObj()
        match buckets.type:
            case commands.BucketType.default:
                bucket_item = "everyone"
            case commands.BucketType.channel:
                fake_msg.channel = bucket_item or ctx.channel
                bucket_item = bucket_item or ctx.channel
            case commands.BucketType.member | commands.BucketType.user:
                fake_msg.guild = (bucket_item or ctx).guild
                fake_msg.author = bucket_item or ctx.author
                bucket_item = bucket_item or ctx.author
            case commands.BucketType.guild:
                fake_msg.guild = bucket_item or ctx.guild
                fake_msg.author = ctx.author
                bucket_item = bucket_item or ctx.guild
            case commands.BucketType.role:
                fake_msg.channel = ctx.channel
                fake_msg.author = FakeObj(top_role=bucket_item) if bucket_item else ctx.author
                bucket_item = bucket_item or (
                    ctx.channel if isinstance(ctx.channel, PrivateChannel) else ctx.author.top_role
                )
            case commands.BucketType.category:
                fake_msg.channel = (
                    FakeObj(category=bucket_item) if bucket_item else ctx.channel.category
                )
                bucket_item = bucket_item or ctx.channel.category or ctx.channel

        if bucket := buckets.get_bucket(fake_msg):
            bucket.reset()
            response = "cooldown_reset"
        else:
            response = "bucket_not_found"
        await ctx.send(ctx._(response).format(mono(str(command)), mono(str(bucket_item))))


class PluginManager(Cog, command_attrs=dict(hidden=True)):
    # fmt: off
    ALREADY_DISABLED       = f"{__module__}.already_disabled"
    ALREADY_ENABLED        = f"{__module__}.already_enabled"
    ALREADY_LOADED         = f"{__module__}.already_loaded"
    DISABLED               = f"{__module__}.disabled"
    ENABLED                = f"{__module__}.enabled"
    INVALID                = "invalid"
    LOADED                 = f"{__module__}.loaded"
    NO_COMMANDS_PROVIDED   = f"{__module__}.no_commands_provided"
    NO_EXTENSIONS_PROVIDED = f"{__module__}.no_extensions_provided"
    NOT_FOUND              = "not_found"
    NOT_LOADED             = f"{__module__}.not_loaded"
    RELOADED               = f"{__module__}.reloaded"
    UNLOADED               = f"{__module__}.unloaded"
    # fmt: on

    def __init__(self, cogs_path: str | PathLike):
        self.COGS_PATH = cogs_path
        self.COGS_PATH_DOTTED = ".".join(Path(self.COGS_PATH).parts)

    async def cog_check(self, ctx: Context) -> bool:
        return await ctx.ara.is_owner(ctx.author)

    @commands.group(invoke_without_command=True)
    async def ext(self, ctx: Context):
        await self.ext_list(ctx)

    @ext.command(name="list")
    async def ext_list(self, ctx: Context):
        trim_amount = len(Path(self.COGS_PATH).parts)
        embed = disnake.Embed(color=Color.YELLOW).add_field(
            ctx._("extensions"),
            "\n".join(module.split(".", trim_amount)[-1] for module in ctx.bot.extensions),
        )
        await ctx.send(embed=embed)

    @ext.command(name="load", aliases=["enable"], usage="<extensions>")
    async def ext_load(self, ctx: Context, *extensions: str):
        if not extensions:
            await ctx.send_(PluginManager.NO_EXTENSIONS_PROVIDED, False)
            return

        statuses = {
            None: ctx._(PluginManager.LOADED, False),
            commands.ExtensionNotFound: ctx._(PluginManager.NOT_FOUND, False),
            ModuleNotFoundError: ctx._(PluginManager.NOT_FOUND, False),
            commands.ExtensionAlreadyLoaded: ctx._(PluginManager.ALREADY_LOADED, False),
            commands.ExtensionFailed: ctx._(PluginManager.INVALID, False),
            commands.NoEntryPointError: ctx._(PluginManager.INVALID, False),
        }
        load = lambda ext: ctx.ara.load_extension(f"{self.COGS_PATH_DOTTED}.{ext}")

        await self._do_action_group_format_embed_send(load, extensions, statuses, ctx)

    @ext.command(name="unload", aliases=["disable"], usage="<extensions>")
    async def ext_unload(self, ctx: Context, *extensions: str):
        if not extensions:
            await ctx.send_(PluginManager.NO_EXTENSIONS_PROVIDED, False)
            return

        statuses = {
            None: ctx._(PluginManager.UNLOADED, False),
            commands.ExtensionNotLoaded: ctx._(PluginManager.NOT_LOADED, False),
        }
        unload = lambda ext: ctx.ara.unload_extension(f"{self.COGS_PATH_DOTTED}.{ext}")
        await self._do_action_group_format_embed_send(unload, extensions, statuses, ctx)

    @ext.command(name="reload", usage="<extensions>")
    async def ext_reload(self, ctx: Context, *extensions: str):
        if not extensions:
            await ctx.send_(PluginManager.NO_EXTENSIONS_PROVIDED, False)
            return

        statuses = {
            None: ctx._(PluginManager.RELOADED, False),
            commands.ExtensionNotFound: ctx._(PluginManager.NOT_FOUND, False),
            ModuleNotFoundError: ctx._(PluginManager.NOT_FOUND, False),
            commands.ExtensionNotLoaded: ctx._(PluginManager.NOT_LOADED, False),
            commands.ExtensionFailed: ctx._(PluginManager.INVALID, False),
            commands.NoEntryPointError: ctx._(PluginManager.INVALID, False),
        }
        reload = lambda ext: ctx.ara.reload_extension(f"{self.COGS_PATH_DOTTED}.{ext}")
        await self._do_action_group_format_embed_send(reload, extensions, statuses, ctx)

    @commands.group(aliases=["command"])
    async def cmd(self, ctx: Context):
        pass

    @cmd.command(name="enable", aliases=["load"], usage="<commands>")
    async def cmd_enable(self, ctx: Context, *cmds: str):
        if not cmds:
            await ctx.send_(PluginManager.NO_COMMANDS_PROVIDED, False)
            return

        statuses = {
            None: ctx._(PluginManager.ENABLED, False),
            commands.CommandNotFound: ctx._(PluginManager.NOT_FOUND, False),
            CommandAlreadyEnabled: ctx._(PluginManager.ALREADY_ENABLED, False),
        }

        def enable(cmd: str) -> None:
            command = ctx.ara.get_command(cmd)
            if not command:
                raise commands.CommandNotFound
            if command.enabled:
                raise CommandAlreadyEnabled
            command.enabled = True

        await self._do_action_group_format_embed_send(enable, cmds, statuses, ctx)

    @cmd.command(name="disable", aliases=["unload"], usage="<commands>")
    async def cmd_disable(self, ctx: Context, *cmds: str):
        if not cmds:
            await ctx.send_(PluginManager.NO_COMMANDS_PROVIDED, False)
            return

        statuses = {
            None: ctx._(PluginManager.DISABLED, False),
            commands.CommandNotFound: ctx._(PluginManager.NOT_FOUND, False),
            commands.DisabledCommand: ctx._(PluginManager.ALREADY_DISABLED, False),
        }

        def disable(cmd: str) -> None:
            command = ctx.ara.get_command(cmd)
            if not command:
                raise commands.CommandNotFound
            if not command.enabled:
                raise commands.DisabledCommand
            command.enabled = False

        await self._do_action_group_format_embed_send(disable, cmds, statuses, ctx)

    @staticmethod
    def group_by_exc_raised[T](
        action: Callable[[T], Any], arguments: Iterable[T]
    ) -> dict[Exception | None, T]:
        mapping = defaultdict(list)
        for arg in arguments:
            try:
                action(arg)
            except Exception as e:
                logging.debug("%s raised for %s", type(e), arg)
                mapping[type(e)].append(arg)
            else:
                mapping[None].append(arg)
        return mapping

    @staticmethod
    def embed_add_groups(embed: disnake.Embed, groups: dict[str, list[str]]) -> disnake.Embed:
        for field_name, items in groups.items():
            if items:
                embed.add_field(field_name, "\n".join(items))
        return embed

    @staticmethod
    def merge_dict_values[T, T2: str, T3](
        key_val: dict[T, T2], key_repr: dict[T, T3]
    ) -> dict[T3, T2]:
        return {key_repr[key]: val for key, val in key_val.items() if val}

    async def _do_action_group_format_embed_send[T](
        self,
        action: Callable[[T], Any],
        arguments: Iterable[T],
        exc_repr: dict[Exception | None, str],
        ctx: Context,
    ) -> None:
        grouped = self.group_by_exc_raised(action, arguments)
        merged = self.merge_dict_values(grouped, exc_repr)
        embed = self.embed_add_groups(disnake.Embed(), merged)
        if embed.fields:
            await ctx.send(embed=embed)
        else:
            await ctx.send_("no_items_provided")


def setup(ara: Ara):
    ara.add_cog(OwnerCommands())
    ara.add_cog(PluginManager(ara._plugins_path))
