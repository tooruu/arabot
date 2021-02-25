from io import StringIO
from textwrap import indent
from traceback import format_exc
from contextlib import redirect_stdout
from discord.ext.commands import command, Cog, check
from ...utils.utils import is_root


class Sample(Cog, name="Admin"):
    def __init__(self, client):
        self.bot = client
        self._last_result = None

    @check(is_root)
    @command(hidden=True, name="eval", aliases=["exec"])
    async def _eval(self, ctx, *, body):

        env = {
            "bot": self.bot,
            "ctx": ctx,
            "_": self._last_result,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = StringIO()

        to_compile = f"async def func():\n{indent(body, '  ')}"

        try:
            exec(to_compile, env)
        except Exception as e:
            await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{format_exc()}\n```")
        else:
            value = stdout.getvalue()

            try:
                if ret is None:
                    if value:
                        await ctx.send(f"```py\n{value}\n```")
                else:
                    self._last_result = ret
                    await ctx.send(f"```py\n{value}{ret}\n```")
                await ctx.message.add_reaction("✅")
            except Exception:
                await ctx.message.add_reaction("❌")

    @staticmethod
    def cleanup_code(content):
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")


def setup(client):
    client.add_cog(Sample(client))
