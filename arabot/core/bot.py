import logging
import os
import re
from collections.abc import Callable, Coroutine, Generator
from copy import copy
from pathlib import Path
from pkgutil import iter_modules
from traceback import format_exception
from typing import Any, override

import aiohttp
import disnake
from disnake.ext import commands
from disnake.ext.commands.bot_base import PrefixType
from disnake.utils import oauth_url, utcnow

from arabot.core.config import Config
from arabot.core.database import Setting, init_db
from arabot.core.enums import SettingKey
from arabot.core.errors import StopCommand
from arabot.core.patches import Context, LocalizationStore
from arabot.core.permissions import (
    PermissionConfigurationError,
    PermissionDenied,
    PermissionService,
    PermissionUnavailable,
)
from arabot.utils import codeblock, mono, system_info, time_in

type MaybeCoro[T] = T | Coroutine[Any, Any, T]
type CommandPrefix = PrefixType | Callable[[Ara, disnake.Message], MaybeCoro[PrefixType]]

logger = logging.getLogger(__name__)


def search_directory(path: str | os.PathLike) -> Generator[str]:
    path = Path(path)

    if ".." in os.path.relpath(path):
        raise ValueError("Paths outside the cwd are not supported")
    if not path.exists():
        raise ValueError(f"Provided path '{path.resolve()}' does not exist")
    if not path.is_dir():
        raise ValueError(f"Provided path '{path.resolve()}' is not a directory")

    def with_prefix(f: str) -> str:
        return ".".join((path / f).parts)

    modules, packages = set[str](), set[str]()
    for _, name, ispkg in iter_modules([str(path)]):
        if not name.startswith("_"):
            (packages if ispkg else modules).add(name)
    dirs = {p.name for p in Path(path).glob("[!_]*/")} - packages

    yield from map(with_prefix, modules)
    yield from map(with_prefix, packages)
    for directory in dirs:
        yield from search_directory(path / directory)


async def prefix_manager(ara: Ara, msg: disnake.Message) -> str | None:
    custom_prefix = await Setting.get(SettingKey.PREFIX, msg.guild.id) or ";"
    quantifier = "+" if custom_prefix[-1].isalpha() else "*"
    pfx_pattern = rf"{re.escape(custom_prefix)}\s{quantifier}|ara\s+|<@!?{ara.user.id}>\s*"
    if msg.guild.self_role:
        pfx_pattern += rf"|<@&{msg.guild.self_role.id}>\s*"
    return (found := re.match(pfx_pattern, msg.content, re.IGNORECASE)) and found[0]


class Ara(commands.Bot):
    i18n: LocalizationStore

    def __init__(
        self,
        *args,
        embed_color: int | disnake.Color | None = None,
        plugins_path: str | os.PathLike = "arabot/plugins",
        l10n_path: str | os.PathLike = "resources/locales",
        token: str | None = None,
        command_prefix: CommandPrefix | None = prefix_manager,
        **kwargs,
    ):
        super().__init__(*args, command_prefix=command_prefix, **kwargs)
        self.http.token = token
        self._plugins_path = Path(plugins_path)
        self._l10n_path = l10n_path
        disnake.Embed.set_default_color(embed_color)
        self.permissions = PermissionService(self)
        self.add_check(self.permissions.prefix_check)
        self.add_check(self.permissions.prefix_check, call_once=True)
        self.add_app_command_check(self.permissions.slash_check, slash_commands=True)
        self.add_app_command_check(self.permissions.slash_check, slash_commands=True, call_once=True)

    def refresh_permissions(self) -> None:
        if hasattr(self, "permissions"):
            self.permissions.registry.refresh()

    @override
    def add_cog(self, cog: commands.Cog, *, override: bool = False) -> None:
        super().add_cog(cog, override=override)
        self.refresh_permissions()

    @override
    def remove_cog(self, name: str) -> commands.Cog | None:
        cog = super().remove_cog(name)
        self.refresh_permissions()
        return cog

    @override
    def add_command(self, command: commands.Command) -> None:
        super().add_command(command)
        self.refresh_permissions()

    @override
    def remove_command(self, name: str) -> commands.Command | None:
        command = super().remove_command(name)
        self.refresh_permissions()
        return command

    @override
    def add_slash_command(self, command: commands.InvokableSlashCommand) -> None:
        super().add_slash_command(command)
        self.refresh_permissions()

    @override
    def remove_slash_command(self, name: str) -> commands.InvokableSlashCommand | None:
        command = super().remove_slash_command(name)
        self.refresh_permissions()
        return command

    @override
    async def invoke(self, ctx: Context) -> None:
        # Discover the leaf without consuming the parser used by disnake itself.
        command = ctx.command
        view = copy(ctx.view)
        while isinstance(command, commands.Group):
            view.skip_ws()
            child = command.all_commands.get(view.get_word())
            if child is None:
                break
            command = child
        ctx.permission_command = command
        await super().invoke(ctx)

    @override
    async def login(self) -> None:
        token = self.http.token or Config.token

        try:
            await super().login(token)
        except (disnake.LoginFailure, TypeError) as e:
            logger.critical("Invalid token %r", token)
            if isinstance(e, TypeError):
                raise disnake.LoginFailure(e) from e
            raise
        except aiohttp.ClientConnectorError:
            logger.critical("Connection error", exc_info=True)
            raise

    @override
    async def _fill_owners(self) -> None:
        if self.owner_id or self.owner_ids:
            return

        await self.wait_until_first_connect()

        app = await self.application_info()
        self.name = app.name

        if app.install_params:
            self.invite_url = app.install_params.to_url()
        else:
            self.invite_url = oauth_url(
                app.id,
                permissions=disnake.Permissions.all(),
                scopes=("bot", "application.commands"),
            )

        if app.team:
            self.owner_id = app.team.owner_id
            self.owner = await self.get_or_fetch_user(self.owner_id)
            self.owners = {
                member
                for member in app.team.members
                if member.role in (disnake.TeamMemberRole.admin, disnake.TeamMemberRole.developer)
            }
            self.owner_ids = {m.id for m in self.owners}
        else:
            self.owner = app.owner
            self.owner_id = app.owner.id

    @override
    async def start(self) -> None:
        async with aiohttp.ClientSession() as self.session, init_db():
            self.i18n.load(self._l10n_path)
            await self.permissions.initialize()
            await self.login()
            self.load_extensions()
            await self.connect()

    @override
    async def get_context[CTX: commands.Context](self, message: disnake.Message, *, cls: type[CTX] = Context) -> CTX:
        return await super().get_context(message, cls=cls)

    @override
    def load_extensions(self) -> None:
        trim_amount = len(self._plugins_path.parts)
        for module in search_directory(self._plugins_path):
            short = module.split(".", maxsplit=trim_amount)[-1]
            try:
                self.load_extension(module)
            except commands.ExtensionFailed as e:
                logger.error("Failed to load %s", short, exc_info=e.original)
            except commands.NoEntryPointError:
                logger.error("No entry point in %s", short)
            except commands.ExtensionNotFound:
                logger.error("Module not found: %s", short)
            else:
                logger.info("Loaded %s", short)

    async def fetch_or_create_imposter_webhook(self, name: str, chl: disnake.TextChannel) -> disnake.Webhook:
        webhooks = await chl.webhooks()

        return disnake.utils.get(webhooks, user=self.user, name=name) or await chl.create_webhook(
            name=name, avatar=self.user.display_avatar
        )

    @override
    async def on_command_error(self, context: Context, exception: disnake.DiscordException) -> None:
        match exception:
            case PermissionDenied():
                await context.reply_("permission_denied", False)
            case PermissionUnavailable():
                await context.reply_("permissions_unavailable", False)
            case PermissionConfigurationError():
                await context.reply(str(exception))
            case commands.CommandOnCooldown(retry_after=retry_after):
                remaining = time_in(retry_after)
                await context.reply(context._("cooldown_expires", False).format(remaining))
            case commands.DisabledCommand():
                await context.reply_("command_disabled")
            case commands.CommandInvokeError(original=aiohttp.ClientResponseError(status=status)) if (
                context.cog.qualified_name.startswith(("Google", "Youtube"))
            ):
                match status:
                    case 403:
                        await context.reply(
                            context._("cloud_billing_disabled").format(
                                mono(context.invoked_with), mono(str(self.owner))
                            )
                        )
                    case 429:
                        await context.send(context._("today_quota_exceeded").format(mono(context.invoked_with)))
            case commands.MissingRequiredArgument():
                await context.send_help(context.command)
            case commands.UserInputError():
                await context.reply_("invalid_argument")
            case (
                StopCommand()
                | commands.BotMissingPermissions()
                | commands.CheckFailure()
                | commands.ExpectedClosingQuoteError()
                | commands.MaxConcurrencyReached()
                | commands.MissingPermissions()
            ):
                if exception.args:
                    await context.reply(exception.args[0])
            case commands.CommandNotFound():
                pass
            case _:
                if isinstance(exception, commands.CommandInvokeError):
                    exception = exception.original
                logger.error("Unhandled exception", exc_info=exception)
                await context.reply_("unknown_error", False)
                if not Config.debug_mode:
                    await self.owner.send(
                        embed=disnake.Embed(
                            title=context.command,
                            description=codeblock("".join(format_exception(exception))),
                            timestamp=utcnow(),
                        ).set_author(name="Error", url=context.message.jump_url)
                    )

    async def on_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, exception: commands.CommandError
    ) -> None:
        if isinstance(exception, commands.CommandInvokeError):
            exception = exception.original
        match exception:
            case PermissionDenied():
                message = inter._("permission_denied", 0)
            case PermissionUnavailable():
                message = inter._("permissions_unavailable", 0)
            case commands.DisabledCommand():
                message = inter._("command_disabled", 0)
            case PermissionConfigurationError() | commands.CheckFailure() | commands.UserInputError():
                message = str(exception) or inter._("permission_denied", 0)
            case commands.CommandOnCooldown(retry_after=retry_after):
                message = inter._("cooldown_expires", 0).format(time_in(retry_after))
            case _:
                logger.error("Unhandled slash command exception", exc_info=exception)
                message = inter._("unknown_error", 0)
        if inter.response.is_done():
            try:
                original = await inter.original_response()
            except disnake.NotFound:
                original = None
            if original and original.flags.ephemeral:
                await inter.edit_original_response(content=message, embed=None, view=None)
            else:
                await inter.followup.send(message, ephemeral=True)
        else:
            await inter.response.send_message(message, ephemeral=True)

    async def on_ready(self) -> None:
        logger.info(system_info())
