import logging
from functools import partial
from io import StringIO
from typing import Any

import disnake
from aiohttp import ClientResponseError
from arabot.core import Ara, Category, Codeblocks, Cog, Context
from arabot.core.utils import codeblock
from disnake.ext import commands

from . import errors
from .client import LocalEval, RemoteEval


class Eval(Cog, category=Category.GENERAL):
    @commands.command(aliases=["exec", "eval", "code", "py"], brief="Evaluate a Python script")
    async def python(self, ctx: Context, *, codeblocks: Codeblocks):
        if not codeblocks:
            await ctx.reply("Send a Python codeblock to evaluate it")
            return

        await ctx.trigger_typing()
        _lang, code = codeblocks.pop(0)
        inputlines = codeblocks[0][1] if codeblocks else None
        result = disnake.Embed(color=0xFFCD3C, description="").set_author(
            name="Python", icon_url="https://python.org/static/favicon.ico"
        )

        if await ctx.ara.is_owner(ctx.author):
            evaluator = LocalEval(
                env=dict(
                    ctx=ctx,
                    msg=ctx.message,
                    message=ctx.message,
                    me=ctx.author,
                    guild=ctx.guild,
                    channel=ctx.channel,
                    ara=ctx.bot,
                    bot=ctx.bot,
                    disnake=disnake,
                    discord=disnake,
                    embed=disnake.Embed(),
                ),
                stdin=StringIO(inputlines),
            )
            result.set_footer(
                text="Powered by myself 😌",
                icon_url=ctx.me.avatar.icon.url,
            )
        else:
            evaluator = RemoteEval(session=ctx.ara.session, stdin=inputlines)
            result.set_footer(
                text="Powered by Piston",
                icon_url="https://raw.githubusercontent.com"
                "/tooruu/AraBot/master/resources/piston.png",
            )

        append_codeblock = partial(self.embed_add_codeblock_with_warnings, result, lang="py")
        try:
            stdout, return_value = await evaluator.run(code)
        except (ClientResponseError, errors.RemoteEvalBadResponse) as e:
            logging.error(e.message)
            self.embed_add_codeblock_with_warnings(result, "Connection error ⚠️", e.message)
        except Exception as e:
            logging.info(e)
            result.title = "Run failed ❌"

            if isinstance(e, errors.EvalException) and getattr(e, "stdout", None):
                append_codeblock("Output", e.stdout)

            if isinstance(e, errors.LocalEvalException):
                append_codeblock("Error", e.format(source=code))
            elif isinstance(e, errors.RemoteEvalException):
                append_codeblock("Error", e.format())
                result.description += f"Exit code: {e.exit_code}\n"
        else:
            result.title = "Run finished ✅"
            append_codeblock("Output", stdout)

            if return_value is not None:
                append_codeblock("Return value", repr(return_value))

        await ctx.reply(embed=result)

    @staticmethod
    def embed_add_codeblock_with_warnings(
        embed: disnake.Embed,
        name: str,
        value: Any,
        lang: str = "",
    ):
        if not (value := str(value).strip()):
            embed.description += f"No {name}.\n".capitalize()
            return

        maxlen = 1000
        if len(value) > maxlen:
            embed.description += f"{name} trimmed to last {maxlen} characters."
        value = codeblock(value[-maxlen:], lang)
        embed.add_field(name, value, inline=False)


def setup(ara: Ara):
    ara.add_cog(Eval())
