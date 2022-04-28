from glob import glob
from itertools import groupby
from os import getenv
from subprocess import check_output

import arabot
from arabot.core import Ara, Category, Cog, Context, utils
from disnake import Embed
from disnake.ext.commands import MinimalHelpCommand, command


class AraHelp(MinimalHelpCommand):
    def __init__(self, **command_attrs):
        super().__init__(command_attrs=command_attrs)

    async def send_bot_help(self, mapping):
        bot: Ara = self.context.bot

        embed = (
            Embed(description=self.get_opening_note() or Embed.Empty)
            .set_author(
                name=f"{bot.name} help",
                icon_url=bot.user.avatar.with_format("png").with_size(128).url,
            )
            .set_thumbnail(url=bot.user.avatar.with_format("png").url)
            .set_footer(text=self.get_ending_note() or Embed.Empty)
        )

        get_category = lambda command: getattr(command.cog, "category", None) or self.no_category
        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)

        for category, commands in groupby(filtered, key=get_category):
            commands = (
                sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            )
            val = ""
            for cmd in commands:
                cell = utils.mono(cmd.name)
                if cmd.brief:
                    cell = f"[{cell}](http://. '{cmd.brief}')"
                if len(val + cell) > 1024:
                    break
                val += cell + " "

            embed.add_field(name=utils.bold(category), value=val[:-1] or "No commands")

        await self.get_destination().send(embed=embed)

    def get_opening_note(self):
        command_name = self.invoked_with
        return (
            f"Use `{self.context.clean_prefix}{command_name} [command]` for more info on a command.\n"
            f"You can also use `{self.context.clean_prefix}{command_name} [category]` for more info on a category."
        )

    def get_ending_note(self):
        return f"{self.context.bot.name} v{arabot.__version__}"


class Meta(Cog, category=Category.META):
    def __setup_help_command(self):
        self._orig_help_command = self.ara.help_command
        self.ara.help_command = AraHelp(aliases=["halp", "h"], brief="Show this message")
        self.ara.help_command.cog = self

    def __set_line_count(self):
        count = 0
        with suppress(OSError):
            for g in glob("arabot/**/*.py", recursive=True):
                with suppress(OSError):
                    with open(g, encoding="utf8") as f:
                        count += len(f.readlines())
        self._line_count = count

    def __set_git_status(self):
        if rev_hash := getenv("HEROKU_SLUG_COMMIT"):
            dirty = False
        else:
            dirty = bool(check_output(["git", "status", "-s"]))
            rev_hash = check_output(["git", "rev-parse", "HEAD", "--"]).decode().strip()
        self._worktree_dirty = dirty
        self._rev_hash = rev_hash
        self._rev_hash_short = rev_hash[:7]

    def __init__(self, ara: Ara):
        self.ara = ara
        self.__setup_help_command()
        self.__set_line_count()
        self.__set_git_status()

    @command(aliases=["ver", "v"], brief="Show bot's version")
    async def version(self, ctx: Context):
        dirty_indicator = "*" if self._worktree_dirty else ""
        ver = f"{ctx.ara.name} v{__version__} `{self._rev_hash_short}{dirty_indicator}`"
        await ctx.send(ver)

    @command()
    async def lines(self, ctx: Context):
        if not self._line_count:
            await ctx.send("Couldn't read files")
            return
        await ctx.send(
            f"{ctx.ara.name} v{__version__} consists of **{self._line_count}** lines of Python code"
        )

    @command(aliases=["github", "gh"])
    async def repo(self, ctx: Context):
        await ctx.send("https://github.com/tooruu/AraBot")

    @command(brief="Show server's invite link")
    async def invite(self, ctx: Context):
        await ctx.send(await ctx.guild.get_unlimited_invite() or "Couldn't find invite link")

    def cog_unload(self):
        self.ara.help_command = self._orig_help_command


def setup(ara: Ara):
    ara.add_cog(Meta(ara))
