import logging
from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, TypeVar

from arabot.core import Ara, Cog, Color, Context
from disnake import Activity, ActivityType, Embed
from disnake.ext import commands

_T = TypeVar("_T")
_T1 = TypeVar("_T1", bound=str)
_T2 = TypeVar("_T2")


class CommandAlreadyEnabled(commands.CommandError):
    pass


class OwnerCommands(Cog, command_attrs=dict(hidden=True)):
    async def cog_check(self, ctx: Context):
        return await ctx.ara.is_owner(ctx.author)

    @commands.command(
        aliases=[
            "exit",
            "quit",
            "kill",
            "shine",
            "shineo",
            "die",
            "kys",
            "begone",
            "fuck",
            "gon",
        ]
    )
    async def stop(self, ctx: Context):
        await ctx.send("I'm dying, master 🥶")
        await ctx.ara.close()

    @commands.command()
    async def presence(self, ctx: Context, act_type="", *, act_name=""):
        acts = {
            "playing": ActivityType.playing,
            "listening": ActivityType.listening,
            "watching": ActivityType.watching,
            "competing": ActivityType.competing,
        }

        if act_type and act_type not in acts:
            await ctx.send("Invalid presence type")
            return

        if act_type and not act_name:
            await ctx.send("You must specify name of activity")
            return

        act = Activity(type=acts[act_type], name=act_name) if act_type else None
        await ctx.ara.change_presence(activity=act)
        await ctx.message.add_reaction("✅")


class PluginManager(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, ara: Ara):
        self.COGS_PATH = ara._default_cogs_path
        self.COGS_PATH_DOTTED = ".".join(Path(self.COGS_PATH).parts)

    async def cog_check(self, ctx: Context):
        return await ctx.ara.is_owner(ctx.author)

    @commands.group(invoke_without_command=True)
    async def ext(self, ctx: Context):
        await self.ext_list(ctx)

    @ext.command(name="list")
    async def ext_list(self, ctx: Context):
        trim_amount = len(Path(self.COGS_PATH).parts)
        embed = Embed(color=Color.yellow).add_field(
            name="Extensions",
            value="\n".join(module.split(".", trim_amount)[-1] for module in ctx.bot.extensions),
        )
        await ctx.send(embed=embed)

    @ext.command(name="load", aliases=["enable"])
    async def ext_load(self, ctx: Context, *extensions):
        if not extensions:
            await ctx.send("No extensions provided")
            return

        statuses = {
            None: "Loaded",
            commands.ExtensionNotFound: "Not found",
            ModuleNotFoundError: "Not found",
            commands.ExtensionAlreadyLoaded: "Already loaded",
            commands.ExtensionFailed: "Invalid",
            commands.NoEntryPointError: "Invalid",
        }
        load = lambda ext: ctx.ara.load_extension(f"{self.COGS_PATH_DOTTED}.{ext}")

        await self.do_action_group_format_embed_send(load, extensions, statuses, ctx.send)

    @ext.command(name="unload", aliases=["disable"])
    async def ext_unload(self, ctx: Context, *extensions):
        if not extensions:
            await ctx.send("No extensions provided")
            return

        statuses = {
            None: "Unloaded",
            commands.ExtensionNotLoaded: "Not loaded",
        }
        unload = lambda ext: ctx.ara.unload_extension(f"{self.COGS_PATH_DOTTED}.{ext}")
        await self.do_action_group_format_embed_send(unload, extensions, statuses, ctx.send)

    @ext.command(name="reload")
    async def ext_reload(self, ctx: Context, *extensions):
        if not extensions:
            await ctx.send("No extensions provided")
            return

        statuses = {
            None: "Reloaded",
            commands.ExtensionNotFound: "Not found",
            ModuleNotFoundError: "Not found",
            commands.ExtensionNotLoaded: "Not loaded",
            commands.ExtensionFailed: "Invalid",
            commands.NoEntryPointError: "Invalid",
        }
        reload = lambda ext: ctx.ara.reload_extension(f"{self.COGS_PATH_DOTTED}.{ext}")
        await self.do_action_group_format_embed_send(reload, extensions, statuses, ctx.send)

    @commands.group(aliases=["command"])
    async def cmd(self, ctx: Context):
        pass

    @cmd.command(name="enable", aliases=["load"])
    async def cmd_enable(self, ctx: Context, *cmds):
        if not cmds:
            await ctx.send("No commands provided")
            return

        statuses = {
            None: "Enabled",
            commands.CommandNotFound: "Not found",
            CommandAlreadyEnabled: "Already enabled",
        }

        def enable(command):
            if cmd := ctx.ara.get_command(command):
                if cmd.enabled:
                    raise CommandAlreadyEnabled
                else:
                    cmd.enabled = True
            else:
                raise commands.CommandNotFound

        await self.do_action_group_format_embed_send(enable, cmds, statuses, ctx.send)

    @cmd.command(name="disable", aliases=["unload"])
    async def cmd_disable(self, ctx: Context, *cmds):
        if not cmds:
            await ctx.send("No commands provided")
            return

        statuses = {
            None: "Disabled",
            commands.CommandNotFound: "Not found",
            commands.DisabledCommand: "Already disabled",
        }

        def disable(command):
            if cmd := ctx.ara.get_command(command):
                if cmd.enabled:
                    cmd.enabled = False
                else:
                    raise commands.DisabledCommand
            else:
                raise commands.CommandNotFound

        await self.do_action_group_format_embed_send(disable, cmds, statuses, ctx.send)

    @staticmethod
    def group_by_exc_raised(
        action: Callable[[_T], Any],
        arguments: Iterable[_T],
    ) -> dict[Exception | None, _T]:
        mapping = defaultdict(list)
        for arg in arguments:
            try:
                action(arg)
            except Exception as e:
                logging.info(f"{type(e)} raised for {arg}")
                mapping[type(e)].append(arg)
            else:
                mapping[None].append(arg)
        return mapping

    @staticmethod
    def embed_add_groups(embed: Embed, groups: dict[str, list[str]]) -> Embed:
        for field, items in groups.items():
            if items:
                embed.add_field(name=field, value="\n".join(items))
        return embed

    @staticmethod
    def merge_dict_values(key_val: dict[_T, _T1], key_repr: dict[_T, _T2]) -> dict[_T2, _T1]:
        return {key_repr[key]: val for key, val in key_val.items() if val}

    async def do_action_group_format_embed_send(
        self,
        action: Callable[[_T], Any],
        arguments: Iterable[_T],
        exc_repr: dict[Exception | None, str],
        send,
    ) -> Embed:
        grouped = self.group_by_exc_raised(action, arguments)
        merged = self.merge_dict_values(grouped, exc_repr)
        embed = self.embed_add_groups(Embed(), merged)
        if embed.fields:
            await send(embed=embed)
        else:
            await send("No items provided")


def setup(ara: Ara):
    ara.add_cog(OwnerCommands())
    ara.add_cog(PluginManager(ara))
