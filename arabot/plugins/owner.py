import logging
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import disnake
from disnake.ext import commands

from arabot.core import Ara, Cog, Color, Context

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from os import PathLike

logger = logging.getLogger(__name__)


class OwnerCommands(Cog, command_attrs=dict(hidden=True)):
    permission_configurable = False

    async def cog_check(self, ctx: Context):
        return await ctx.ara.is_owner(ctx.author)

    @commands.command(usage="[activity]")
    async def presence(self, ctx: Context, act_type: str | None = None, *, act_name: str | None = None):
        acts = {
            "playing": disnake.ActivityType.playing,
            "listening": disnake.ActivityType.listening,
            "watching": disnake.ActivityType.watching,
            "competing": disnake.ActivityType.competing,
            "custom": disnake.ActivityType.custom,
            None: None,
        }

        if act_type and act_type not in acts:
            await ctx.send_("invalid_presence")
            return

        if act_type and not act_name:
            await ctx.send_("no_activity")
            return

        match acts[act_type]:
            case None:
                act = None
            case disnake.ActivityType.custom:
                act = disnake.CustomActivity(act_name)
            case activity_type:
                act = disnake.Activity(type=activity_type, name=act_name)

        await ctx.ara.change_presence(activity=act)
        await ctx.tick()


class PluginManager(Cog, command_attrs=dict(hidden=True)):
    permission_configurable = False

    # fmt: off
    ALREADY_LOADED         = f"{__module__}.already_loaded"
    INVALID                = "invalid"
    LOADED                 = f"{__module__}.loaded"
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

    @staticmethod
    def group_by_exc_raised[T](action: Callable[[T], Any], arguments: Iterable[T]) -> dict[Exception | None, T]:
        mapping = defaultdict(list)
        for arg in arguments:
            try:
                action(arg)
            except Exception as e:
                logger.debug("%s raised for %s", type(e), arg)
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
    def merge_dict_values[T, T2: str, T3](key_val: dict[T, T2], key_repr: dict[T, T3]) -> dict[T3, T2]:
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
