import asyncio
import datetime
import logging
import os
import re
from functools import partial
from io import StringIO

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
        brief="Execute a Python script",
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
                # Context vars
                ara=ctx.bot,
                bot=ctx.bot,
                channel=ctx.channel,
                ctx=ctx,
                db=ctx.ara.db,
                guild=ctx.guild,
                me=ctx.author,
                message=ctx.message,
                msg=ctx.message,
                server=ctx.guild,
                # Disnake SDK
                commands=commands,
                discord=disnake,
                disnake=disnake,
                E=disnake.Embed,
                Embed=disnake.Embed,
                utils=disnake.utils,
                # Standard library
                aio=asyncio,
                date=datetime.date,
                datetime=datetime.datetime,
                os=os,
                re=re,
                time=datetime.time,
                timedelta=datetime.timedelta,
            )
            evaluator = LocalEval(env=local_eval_env, stdin=StringIO(inputlines))
            result.set_footer(
                text=ctx._("powered_by", False).format("myself 😌"),
                icon_url=ctx.me.display_avatar.as_icon.compat,
            )
        else:
            evaluator = RemoteEval(session=ctx.ara.session, stdin=inputlines)
            result.set_footer(
                text=ctx._("powered_by", False).format("Piston"),
                icon_url="https://raw.githubusercontent.com"
                "/tooruu/arabot/master/resources/piston.png",
            )

        append_codeblock = partial(self.embed_add_codeblock_with_warnings, result, lang="py")
        try:
            stdout, return_value = await evaluator.run(code)
        except (ClientResponseError, errors.RemoteEvalBadResponse) as e:
            logging.error(e.message)
            self.embed_add_codeblock_with_warnings(result, ctx._("connection_error"), e.message)
        except Exception as e:
            logging.info(e)
            result.title = ctx._("run_failed")

            if isinstance(e, errors.EvalException) and getattr(e, "stdout", None):
                append_codeblock(ctx._("output", False), e.stdout)

            if isinstance(e, errors.LocalEvalException):
                append_codeblock(ctx._("error", False), e.format(source=code))
            elif isinstance(e, errors.RemoteEvalException):
                append_codeblock(ctx._("error", False), e.format())
                result.description += f"{ctx._('exit_code')}: {e.exit_code}\n"
        else:
            result.title = ctx._("run_finished")
            append_codeblock(ctx._("output", False), stdout)

            if return_value is not None:
                append_codeblock(ctx._("return_value"), repr(return_value))
            elif not result.fields:
                await ctx.tick()
                return

        await ctx.reply(embed=result)

    @staticmethod
    def embed_add_codeblock_with_warnings(
        embed: disnake.Embed,
        name: str,
        value: str,
        lang: str = "",
    ) -> None:
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
