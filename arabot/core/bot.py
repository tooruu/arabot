import asyncio
import logging
import os
import sys
from collections.abc import Generator
from datetime import timedelta
from glob import glob
from pathlib import Path
from pkgutil import iter_modules

import aiohttp
import disnake
from disnake.ext import commands

from ..utils import MissingEnvVar, getkeys, mono, strfdelta, system_info
from .errors import StopCommand
from .patches import Context


def search_directory(path) -> Generator[str, None, None]:
    path = Path(path)

    if ".." in os.path.relpath(path):
        raise ValueError("Paths outside the cwd are not supported")
    if not path.exists():
        raise ValueError(f"Provided path '{path.resolve()}' does not exist")
    if not path.is_dir():
        raise ValueError(f"Provided path '{path.resolve()}' is not a directory")

    with_prefix = lambda f: ".".join((path / f).parts)

    modules, packages = set(), set()
    for _, name, ispkg in iter_modules([str(path)]):
        if not name.startswith("_"):
            (packages if ispkg else modules).add(name)
    dirs = {dir.rstrip(os.sep) for dir in glob("[!_]*/", root_dir=path)} - packages

    yield from map(with_prefix, modules)
    yield from map(with_prefix, packages)
    for directory in dirs:
        yield from search_directory(path / directory)


class Ara(commands.Bot):
    def __init__(self, *args, **kwargs):
        self._cogs_path: str = kwargs.pop("cogs_path", "arabot/modules")
        embed_color: int | disnake.Color | None = kwargs.pop("embed_color", None)

        disnake.Embed.set_default_color(embed_color)
        super().__init__(*args, **kwargs)

    async def login(self) -> None:
        try:
            token = getkeys("token")[0]
            await super().login(token)
        except MissingEnvVar:
            logging.critical("Missing environment variable 'token'")
            sys.exit(69)
        except (disnake.LoginFailure, TypeError):
            logging.critical("Invalid token %r", token)
            sys.exit(69)
        except aiohttp.ClientConnectorError:
            logging.critical("No internet connection")
            sys.exit(69)

    async def _fill_owners(self) -> None:
        if self.owner_id or self.owner_ids:
            return

        await self.wait_until_first_connect()

        app = await self.application_info()
        self.name = app.name
        if app.team:
            self.owners = set(app.team.members)
            self.owner_ids = {m.id for m in app.team.members}
        else:
            self.owner = app.owner
            self.owner_id = app.owner.id

    async def start(self) -> None:
        async with aiohttp.ClientSession() as self.session:
            await self.login()
            self.load_extensions()
            await self.connect()

    async def close(self) -> None:
        if self.is_closed():
            return

        logging.info("Bot is shutting down..")
        try:
            await super().close()
        finally:
            pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    async def get_context(self, message: disnake.Message, *, cls=Context) -> Context:
        return await super().get_context(message, cls=cls)

    def load_extensions(self) -> None:
        trim_amount = len(Path(self._cogs_path).parts)
        for module in search_directory(self._cogs_path):
            short = module.split(".", maxsplit=trim_amount)[-1]
            try:
                self.load_extension(module)
            except commands.ExtensionFailed as e:
                logging.error("Failed to load %s", short, exc_info=e.original)
            except commands.NoEntryPointError:
                logging.error("No entry point in %s", short)
            except commands.ExtensionNotFound:
                logging.error("Module not found: %s", short)
            else:
                logging.info("Loaded %s", short)

    async def on_command_error(self, context: Context, exception: disnake.DiscordException) -> None:
        match exception:
            case commands.CommandOnCooldown():
                if exception.retry_after > 60:
                    remaining = strfdelta(timedelta(seconds=exception.retry_after))
                else:
                    remaining = f"{exception.retry_after:.0f} seconds"
                await context.reply(f"Cooldown expires in {remaining}")
            case commands.DisabledCommand():
                await context.reply("This command is disabled!")
            case commands.MaxConcurrencyReached(number=n):
                await context.reply(
                    "Another instance of this command is already running"
                    if n == 1
                    else f"{n} instances of this command are already running"
                )
            case commands.MissingPermissions():
                if not context.command.hidden:
                    await context.reply("Missing permissions")
            case commands.CommandInvokeError(
                original=aiohttp.ClientResponseError(status=status)
            ) if context.cog.qualified_name.startswith(("Google", "Youtube")):
                match status:
                    case 403:
                        await context.reply(
                            f"{mono(context.invoked_with)} doesn't work without "
                            f"cloud-billing,\nask `{mono(self.owner)}` to enable it."
                        )
                    case 429:
                        await context.send(
                            f"Sorry, I've exceeded today's quota for {mono(context.invoked_with)}"
                        )
            case commands.MissingRequiredArgument():
                await context.send_help(context.command)
            case commands.UserInputError():
                await context.reply("Invalid argument")
            case (
                StopCommand()
                | commands.CommandNotFound()
                | commands.CheckFailure()
                | commands.ExpectedClosingQuoteError()
            ):
                pass
            case _:
                logging.error("Unhandled exception", exc_info=exception)
                await context.reply("An error occurred")

    async def on_ready(self) -> None:
        logging.info(system_info())
