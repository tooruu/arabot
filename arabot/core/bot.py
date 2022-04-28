from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
from collections.abc import Generator
from glob import glob
from pathlib import Path
from pkgutil import iter_modules

import aiohttp
import disnake
from arabot import TESTING
from disnake.ext import commands

from .patches import Context
from .utils import MissingEnvVar, getkeys, mono, system_info


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
    for dir in dirs:
        yield from search_directory(path / dir)


async def prefix_manager(ara: Ara, msg: disnake.Message) -> str | None:
    pfx_pattern = r"a; *" if TESTING else rf"; *|ara +|<@!?{ara.user.id}> *"
    if found := re.match(pfx_pattern, msg.content, re.IGNORECASE):
        return found.group()


class Ara(commands.Bot):
    _default_cogs_path = "arabot/cogs"

    def __init__(self, *args, **kwargs):
        activity = disnake.Activity(type=disnake.ActivityType.competing, name="McDonalds")

        intents = disnake.Intents(
            guilds=True,
            members=True,
            emojis_and_stickers=True,
            voice_states=True,
            guild_messages=True,
            guild_reactions=True,
        )

        default_kwargs = dict(
            activity=activity,
            allowed_mentions=disnake.AllowedMentions.none(),
            case_insensitive=True,
            command_prefix=prefix_manager,
            intents=intents,
        )

        if TESTING:
            default_kwargs |= dict(
                reload=True,
                test_guilds=[676889696302792774, 933568919413866526, 954134299119091772],
            )

        super().__init__(*args, **default_kwargs | kwargs)
        disnake.Embed.set_default_color(0xE91E63)

    async def login(self):
        try:
            token = getkeys("token")[0]
            await super().login(token)
        except MissingEnvVar:
            logging.critical("Missing environment variable 'token'")
            sys.exit(69)
        except (disnake.LoginFailure, TypeError):
            logging.critical("Invalid token")
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

    async def start(self):
        async with aiohttp.ClientSession() as self.session:
            await self.login()
            self.load_extensions()
            await self.connect()

    async def close(self):
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

    async def get_context(self, message: disnake.Message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    def load_extensions(self, path: str = _default_cogs_path) -> None:
        trim_amount = len(Path(path).parts)
        for module in search_directory(path):
            short = module.split(".", maxsplit=trim_amount)[-1]
            try:
                self.load_extension(module)
            except commands.ExtensionFailed as e:
                logging.error(f"Failed to load {short}", exc_info=e.original)
            except commands.NoEntryPointError:
                logging.error(f"No entry point in {short}")
            except commands.ExtensionNotFound:
                logging.error(f"Module not found: {short}")
            else:
                logging.info(f"Loaded {short}")

    async def on_command_error(self, ctx: Context, error: disnake.DiscordException) -> None:
        if hasattr(ctx.command, "on_error"):
            return

        match error:
            case commands.CommandOnCooldown():
                await ctx.reply(f"Cooldown expires in {error.retry_after:.0f} seconds")
            case commands.DisabledCommand():
                await ctx.reply("This command is disabled!")
            case commands.MaxConcurrencyReached(number=n):
                await ctx.reply(
                    "Another instance of this command is already running"
                    if n == 1
                    else f"{n} instances of this command are already running"
                )
            case commands.MissingPermissions():
                if not ctx.command.hidden:
                    await ctx.reply("Missing permissions")
            case commands.CommandInvokeError(
                original=aiohttp.ClientResponseError(status=status)
            ) if ctx.cog.qualified_name in ("GSearch", "ImageSearch", "Translate", "TextToSpeech"):
                match status:
                    case 403:
                        await ctx.reply(
                            f"{mono(ctx.invoked_with)} doesn't work without "
                            f"cloud-billing,\nask `{self.owner}` to enable it."
                        )
                    case 429:
                        await ctx.send(
                            f"Sorry, I've exceeded today's quota for {mono(ctx.invoked_with)}"
                        )
            case commands.MissingRequiredArgument():
                await ctx.reply("Missing required argument")
            case commands.UserInputError():
                await ctx.reply("Invalid argument")
            case (
                commands.CommandNotFound()
                | commands.CheckFailure()
                | commands.ExpectedClosingQuoteError()
            ):
                pass
            case _:
                logging.error("Unhandled exception", exc_info=error)
                await ctx.reply("An error occurred")

    async def on_ready(self) -> None:
        logging.info(system_info())
