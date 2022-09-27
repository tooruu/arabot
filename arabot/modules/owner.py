import logging
from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Awaitable, TypeVar

import disnake
from disnake.abc import PrivateChannel
from disnake.ext import commands

from arabot.core import Ara, Cog, Color, Context
from arabot.utils import CIMember, CIRole, CITextChl, Empty, mono

_T = TypeVar("_T")
_T1 = TypeVar("_T1", bound=str)
_T2 = TypeVar("_T2")


class FakeObj:
    def __init__(self, **kwargs):
        for key, value in kwargs.values():
            setattr(self, key, value)


class CommandAlreadyEnabled(commands.CommandError):
    pass


class OwnerCommands(Cog, command_attrs=dict(hidden=True)):
    async def cog_check(self, ctx: Context):  # pylint: disable=invalid-overridden-method
        return await ctx.ara.is_owner(ctx.author)

    @commands.command(
        aliases=[
            "exit",
            "quit",
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
        await ctx.send_("I'm dying, master 🥶")
        await ctx.ara.close()

    @commands.command(usage="[activity]")
    async def presence(self, ctx: Context, act_type="", *, act_name=""):
        acts = {
            "playing": disnake.ActivityType.playing,
            "listening": disnake.ActivityType.listening,
            "watching": disnake.ActivityType.watching,
            "competing": disnake.ActivityType.competing,
        }

        if act_type and act_type not in acts:
            await ctx.send_("Invalid presence type")
            return

        if act_type and not act_name:
            await ctx.send_("You must specify name of activity")
            return

        act = disnake.Activity(type=acts[act_type], name=act_name) if act_type else None
        await ctx.ara.change_presence(activity=act)
        await ctx.tick()

    @commands.command(usage="<command> [bucket item]")
    async def resetcd(
        self,
        ctx: Context,
        input_cmd,
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
            await ctx.send(ctx._("Command {} not found").format(mono(input_cmd)))
            return
        buckets = command._buckets
        if not buckets.valid:
            await ctx.send(ctx._("Command {} has no cooldown").format(mono(command)))
            return
        if not isinstance(buckets.type, commands.BucketType):
            await ctx.send(
                ctx._("Only `BucketType` is supported, got `{}`").format(buckets.type.__name__)
            )
            return
        if bucket_item is None:
            argument = ctx.argument_only.removeprefix(input_cmd + " ")
            await ctx.send(ctx._("Bucket item {} not found").format(mono(argument)))
            return
        if (
            bucket_item
            and buckets.type.name.lower() not in type(bucket_item).__name__.lower()
            and not (
                buckets.type is commands.BucketType.user and isinstance(bucket_item, disnake.Member)
            )
        ):
            await ctx.send(
                ctx._("Bucket type `{}` doesn't match argument type `{}`").format(
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
            response = "{}'s cooldown has been reset for {}"
        else:
            response = "{}'s bucket for {} not found"
        await ctx.send(ctx._(response).format(mono(command), mono(bucket_item)))


class PluginManager(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, ara: Ara):
        self.COGS_PATH = ara._cogs_path
        self.COGS_PATH_DOTTED = ".".join(Path(self.COGS_PATH).parts)

    async def cog_check(self, ctx: Context):  # pylint: disable=invalid-overridden-method
        return await ctx.ara.is_owner(ctx.author)

    @commands.group(invoke_without_command=True)
    async def ext(self, ctx: Context):
        await self.ext_list(ctx)

    @ext.command(name="list")
    async def ext_list(self, ctx: Context):
        trim_amount = len(Path(self.COGS_PATH).parts)
        embed = disnake.Embed(color=Color.yellow).add_field(
            ctx._("Extensions"),
            "\n".join(module.split(".", trim_amount)[-1] for module in ctx.bot.extensions),
        )
        await ctx.send(embed=embed)

    @ext.command(name="load", aliases=["enable"], usage="<extensions>")
    async def ext_load(self, ctx: Context, *extensions):
        if not extensions:
            await ctx.send_("No extensions provided")
            return

        statuses = {
            None: ctx._("Loaded"),
            commands.ExtensionNotFound: ctx._("Not found"),
            ModuleNotFoundError: ctx._("Not found"),
            commands.ExtensionAlreadyLoaded: ctx._("Already loaded"),
            commands.ExtensionFailed: ctx._("Invalid"),
            commands.NoEntryPointError: ctx._("Invalid"),
        }
        load = lambda ext: ctx.ara.load_extension(f"{self.COGS_PATH_DOTTED}.{ext}")

        await self.do_action_group_format_embed_send(load, extensions, statuses, ctx.send)

    @ext.command(name="unload", aliases=["disable"], usage="<extensions>")
    async def ext_unload(self, ctx: Context, *extensions):
        if not extensions:
            await ctx.send_("No extensions provided")
            return

        statuses = {
            None: ctx._("Unloaded"),
            commands.ExtensionNotLoaded: ctx._("Not loaded"),
        }
        unload = lambda ext: ctx.ara.unload_extension(f"{self.COGS_PATH_DOTTED}.{ext}")
        await self.do_action_group_format_embed_send(unload, extensions, statuses, ctx.send)

    @ext.command(name="reload", usage="<extensions>")
    async def ext_reload(self, ctx: Context, *extensions):
        if not extensions:
            await ctx.send_("No extensions provided")
            return

        statuses = {
            None: ctx._("Reloaded"),
            commands.ExtensionNotFound: ctx._("Not found"),
            ModuleNotFoundError: ctx._("Not found"),
            commands.ExtensionNotLoaded: ctx._("Not loaded"),
            commands.ExtensionFailed: ctx._("Invalid"),
            commands.NoEntryPointError: ctx._("Invalid"),
        }
        reload = lambda ext: ctx.ara.reload_extension(f"{self.COGS_PATH_DOTTED}.{ext}")
        await self.do_action_group_format_embed_send(reload, extensions, statuses, ctx.send)

    @commands.group(aliases=["command"])
    async def cmd(self, ctx: Context):
        pass

    @cmd.command(name="enable", aliases=["load"], usage="<commands>")
    async def cmd_enable(self, ctx: Context, *cmds):
        if not cmds:
            await ctx.send_("No commands provided")
            return

        statuses = {
            None: "Enabled",
            commands.CommandNotFound: "Not found",
            CommandAlreadyEnabled: "Already enabled",
        }

        def enable(cmd: str):
            command = ctx.ara.get_command(cmd)
            if not command:
                raise commands.CommandNotFound
            if command.enabled:
                raise CommandAlreadyEnabled
            command.enabled = True

        await self.do_action_group_format_embed_send(enable, cmds, statuses, ctx.send)

    @cmd.command(name="disable", aliases=["unload"], usage="<commands>")
    async def cmd_disable(self, ctx: Context, *cmds):
        if not cmds:
            await ctx.send_("No commands provided")
            return

        statuses = {
            None: "Disabled",
            commands.CommandNotFound: "Not found",
            commands.DisabledCommand: "Already disabled",
        }

        def disable(cmd: str):
            command = ctx.ara.get_command(cmd)
            if not command:
                raise commands.CommandNotFound
            if not command.enabled:
                raise commands.DisabledCommand
            command.enabled = False

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
                logging.info("%s raised for %s", type(e), arg)
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
    def merge_dict_values(key_val: dict[_T, _T1], key_repr: dict[_T, _T2]) -> dict[_T2, _T1]:
        return {key_repr[key]: val for key, val in key_val.items() if val}

    async def do_action_group_format_embed_send(
        self,
        action: Callable[[_T], Any],
        arguments: Iterable[_T],
        exc_repr: dict[Exception | None, str],
        sender: Callable[..., Awaitable[disnake.Message]],
    ) -> None:
        grouped = self.group_by_exc_raised(action, arguments)
        merged = self.merge_dict_values(grouped, exc_repr)
        embed = self.embed_add_groups(disnake.Embed(), merged)
        if embed.fields:
            await sender(embed=embed)
        else:
            await sender("No items provided")


def setup(ara: Ara):
    ara.add_cog(OwnerCommands())
    ara.add_cog(PluginManager(ara))
