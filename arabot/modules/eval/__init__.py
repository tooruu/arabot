import asyncio
import logging
from functools import partial
from io import StringIO
from typing import Any

import disnake
from aiohttp import ClientResponseError
from disnake.ext import commands

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import Codeblocks, codeblock

from . import errors
from .client import LocalEval, RemoteEval


class Eval(Cog, category=Category.GENERAL):
    @commands.cooldown(5, 1)
    @commands.command(
        aliases=["exec", "eval", "code", "py", "run"],
        brief="Evaluate a Python script",
        usage="<codeblock> [input block]",
    )
    async def python(self, ctx: Context, *, codeblocks: Codeblocks):
        await ctx.trigger_typing()
        codeblocks = codeblocks or [("", ctx.argument_only)]
        _lang, code = codeblocks.pop(0)
        inputlines = codeblocks[0][1] if codeblocks else None
        result = disnake.Embed(color=0xFFCD3C, description="").set_author(
            name="Python", icon_url="https://python.org/static/favicon.ico"
        )

        if await ctx.ara.is_owner(ctx.author):
            local_eval_env = dict(
                ctx=ctx,
                message=ctx.message,
                msg=ctx.message,
                me=ctx.author,
                guild=ctx.guild,
                channel=ctx.channel,
                bot=ctx.bot,
                ara=ctx.bot,
                db=ctx.ara.db,
                disnake=disnake,
                discord=disnake,
                commands=commands,
                utils=disnake.utils,
                Embed=disnake.Embed,
                E=disnake.Embed,
                sleep=asyncio.sleep,
            )
            evaluator = LocalEval(env=local_eval_env, stdin=StringIO(inputlines))
            result.set_footer(
                text="Powered by myself 😌", icon_url=ctx.me.display_avatar.as_icon.compat
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
            elif not result.fields:
                await ctx.tick()
                return

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
