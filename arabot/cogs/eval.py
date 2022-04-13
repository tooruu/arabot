import ast
import inspect
import logging
import re
import sys
import traceback
from abc import abstractmethod
from collections.abc import Sequence
from contextlib import redirect_stdout
from functools import partial
from io import StringIO
from types import CodeType
from typing import Any, Protocol

import disnake
from aiohttp import ClientResponseError, ClientSession
from arabot.core import Ara, Cog, Context
from arabot.utils import Category, Codeblocks, Lockable, codeblock, stdin_from
from disnake.ext import commands


class Evaluator(Protocol):
    TB_FILENAME = "<repl>"

    @abstractmethod
    async def run(self, code: str, *args, **kwargs) -> tuple[str, Any]:
        ...


class EvalException(Exception):
    pass


class LocalEvalException(EvalException):
    def __init__(self, error: BaseException):
        self.original = error

    def format(self, *, source: str | Sequence = "", filename: str = Evaluator.TB_FILENAME) -> str:
        if isinstance(source, str):
            source = source.strip().splitlines()

        # tb_header = "Traceback (most recent call last):\n"
        # tb_frames = traceback.extract_tb(self.original.__traceback__)
        # tb_repl_frames = []
        # for frame in tb_frames:
        #     if frame.filename != filename:
        #         continue
        #     if sourcelines:
        #         frame._line = sourcelines[frame.lineno - 1]
        #     tb_repl_frames.append(frame)
        # tb_repl_frames = traceback.format_list(tb_repl_frames)
        # exc_msg = traceback.format_exception_only(self.original)
        # tb_formatted = tb_header + "".join(tb_repl_frames + exc_msg)

        tb = traceback.TracebackException.from_exception(self.original)
        tb_repl_frames = []
        for frame in tb.stack:
            if frame.filename != filename:
                continue
            if source:
                frame._line = source[frame.lineno - 1]
            tb_repl_frames.append(frame)
        tb.stack = traceback.StackSummary.from_list(tb_repl_frames)
        tb_formatted = "".join(tb.format(chain=False))

        return tb_formatted


class RemoteEvalException(EvalException):
    def __init__(self, error: str, output_before_error: str = "", exit_code: int = 1):
        self.error = error
        self.stdout = output_before_error
        self.exit_code = exit_code

    def format(self, *, filename: str = Evaluator.TB_FILENAME) -> str:
        tb_formatted = re.sub(
            r'(?<=^  File ")/piston/jobs/[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}/[^/]+?(?=")',
            filename,
            self.error,
            flags=re.MULTILINE,
        )
        return tb_formatted


class RemoteEvalBadResponse(Exception):
    def __init__(self, message: str):
        self.message = message


class LocalEvalCompileException(LocalEvalException):
    pass


class LocalEvalExecuteException(LocalEvalException):
    def __init__(self, error: BaseException, output_before_error: str = ""):
        super().__init__(error)
        self.stdout = output_before_error


class RemoteEval(Evaluator):
    API = "https://emkc.org/api/v2/piston/execute"

    def __init__(self, *, session: ClientSession = None, stdin: str = ""):
        self.session = session or ClientSession()
        self.stdin = stdin

    async def fetch_response(self, code: str, *, stdin: str | None = None):
        options = {
            "language": "python",
            "version": "3",
            "files": [{"name": self.TB_FILENAME, "content": code}],
            "stdin": stdin or self.stdin,
        }
        async with self.session.post(self.API, json=options) as response:
            metadata = await response.json()

        if "message" in metadata:
            raise RemoteEvalBadResponse(metadata["message"])

        response.raise_for_status()

        return metadata["run"]

    async def run(self, code: str, *, stdin: str | None = None) -> tuple[str, None]:
        data = await self.fetch_response(code, stdin=stdin or self.stdin)
        stdout = data["stdout"]
        exit_code = data["code"]

        if exit_code:
            raise RemoteEvalException(data["stderr"], stdout, exit_code)

        return stdout, None


class LocalEval(Lockable, Evaluator):
    def __init__(self, *, env: dict | None = None, stdin=None):
        self.env = env or {}
        self.stdin = stdin or sys.stdin

    def compile(self, code: str | bytes, flags=None) -> CodeType:
        compile_for = partial(compile, code, self.TB_FILENAME, flags=flags or 0)
        try:
            try:
                return compile_for("eval")
            except SyntaxError:
                return compile_for("exec")
        except BaseException as exc:
            raise LocalEvalCompileException(exc) from exc

    async def execute(self, compiled_code: CodeType) -> tuple[str, Any]:
        output_buffer = StringIO()
        try:
            with stdin_from(self.stdin), redirect_stdout(output_buffer):
                if compiled_code.co_flags & inspect.CO_COROUTINE:
                    r = await eval(compiled_code, self.env)
                else:
                    r = eval(compiled_code, self.env)
        except BaseException as exc:
            stdout = output_buffer.getvalue()
            raise LocalEvalExecuteException(exc, stdout) from exc
        else:
            stdout = output_buffer.getvalue()
            return stdout, r

    async def run(self, code: str, *, env: dict | None = None, stdin=None) -> tuple[str, Any]:
        with self.lock(env=env or self.env, stdin=stdin or self.stdin):
            to_run = self.compile(code, ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            return await self.execute(to_run)


class Eval(Cog, category=Category.GENERAL):
    @commands.command(aliases=["exec", "eval", "code", "py"], brief="Evaluate a Python script")
    async def python(self, ctx: Context, *, codeblocks: Codeblocks):
        if not codeblocks:
            await ctx.reply("Send a Python codeblock to evaluate it")
            return

        await ctx.trigger_typing()
        lang, code = codeblocks.pop(0)
        inputlines = codeblocks[0][1] if codeblocks else None
        result = disnake.Embed(color=0xFFCD3C, description="").set_author(
            name="Python", icon_url="https://python.org/static/favicon.ico"
        )

        if await ctx.ara.is_owner(ctx.author):
            evaluator = LocalEval(
                env=dict(
                    ctx=ctx,
                    msg=ctx.message,
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
                icon_url=ctx.ara.user.avatar.with_size(32).url,
            )
        else:
            evaluator = RemoteEval(session=ctx.ara.session, stdin=inputlines)
            result.set_footer(
                text="Powered by Piston",
                icon_url="https://raw.githubusercontent.com/tooruu/AraBot/master/resources/piston.png",
            )

        append_codeblock = partial(self.embed_add_codeblock_with_warnings, result, lang="py")
        try:
            stdout, return_value = await evaluator.run(code)
        except (ClientResponseError, RemoteEvalBadResponse) as e:
            logging.error(e.message)
            self.embed_add_codeblock_with_warnings(result, "Connection error ⚠️", e.message)
        except Exception as e:
            logging.info(e)
            result.title = "Run failed ❌"

            if isinstance(e, EvalException) and getattr(e, "stdout", None):
                append_codeblock("Output", e.stdout)

            if isinstance(e, LocalEvalException):
                append_codeblock("Error", e.format(source=code))
            elif isinstance(e, RemoteEvalException):
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

        MAXLEN = 1000
        if len(value) > MAXLEN:
            embed.description += f"{name} trimmed to last {MAXLEN} characters."
        value = codeblock(value[-MAXLEN:], lang)
        embed.add_field(name=name, value=value, inline=False)


def setup(ara: Ara):
    ara.add_cog(Eval())
