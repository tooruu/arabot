from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path
from traceback import format_exception

import aiohttp
import disnake
from arabot.utils import DEBUG, MissingEnvVar, getkeys, mono, search_directory, system_info
from disnake import DiscordException
from disnake.ext import commands

from .rewrites import Context, ContextMixin


class Ara(ContextMixin, commands.Bot):
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

        async def prefix_manager(ara: Ara, msg: disnake.Message) -> str | None:
            pfx_pattern = r"a; *" if DEBUG else rf"; *|ara +|<@!?{ara.user.id}> *"
            if found := re.match(pfx_pattern, msg.content, re.IGNORECASE):
                return found.group().strip()

        default_kwargs = dict(
            activity=activity,
            allowed_mentions=disnake.AllowedMentions.none(),
            case_insensitive=True,
            command_prefix=prefix_manager,
            intents=intents,
            owner_id=447138372121788417,
        )

        if DEBUG:
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

    async def start(self):
        await self.login()
        appinfo = await self.application_info()
        self.name = appinfo.name
        self.owner = appinfo.owner
        async with aiohttp.ClientSession() as self.session:
            self.load_extensions()
            await self.connect()

    async def close(self):
        logging.info("Bot is shutting down..")
        try:
            await super().close()
        finally:
            pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    def load_extensions(self, path: str = _default_cogs_path) -> None:
        trim_amount = len(Path(path).parts)
        for module in search_directory(path):
            short = module.split(".", maxsplit=trim_amount)[-1]
            try:
                self.load_extension(module)
            except commands.ExtensionFailed as e:
                logging.error(e)
            except commands.NoEntryPointError:
                logging.error(f"No entry point in {short}")
            except commands.ExtensionNotFound:
                logging.error(f"Module not found: {short}")
            else:
                logging.info(f"Loaded {short}")

    async def on_command_error(self, ctx: Context, error: DiscordException) -> None:
        format_error = lambda e: "".join(format_exception(e))

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
            case commands.CommandInvokeError(original=cause):
                match cause:
                    case aiohttp.ClientResponseError(status=status):
                        match status:
                            case 403:
                                await ctx.reply(
                                    f"{mono(ctx.invoked_with)} doesn't work without "
                                    f"cloud-billing,\nask `{self.owner}` to enable it."
                                )
                            case _:
                                logging.error(f"CmdInvErr:CliResErr: {format_error(cause)}")
                                await ctx.reply("A network error occurred")
                    case _:
                        logging.error(f"CmdInvErr: {format_error(cause)}")
                        await ctx.reply("An error occurred")
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
                logging.error(format_error(error))
                await ctx.reply("An error occurred")
                raise error

    async def on_ready(self) -> None:
        logging.info(system_info())
