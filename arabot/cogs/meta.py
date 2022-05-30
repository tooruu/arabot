from glob import glob
from itertools import groupby
from os import getenv
from subprocess import SubprocessError, check_output
from urllib.parse import urlencode

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
                icon_url=self.context.me.display_avatar.as_icon.compat.url,
            )
            .set_thumbnail(url=bot.user.avatar.compat.url)
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
                val += f"{cell} "

            embed.add_field(utils.bold(category), val[:-1] or "No commands")

        await self.get_destination().send(embed=embed)

    def get_opening_note(self):
        command_repr = self.context.clean_prefix + self.invoked_with
        return (
            f"Use `{command_repr} [command]` for more info on a command.\n"
            f"You can also use `{command_repr} [category]` for more info on a category."
        )

    def get_ending_note(self):
        return f"{self.context.bot.name} v{arabot.__version__}"


class Meta(Cog, category=Category.META):
    def __init__(self, ara: Ara):
        self.ara = ara
        self.__setup_help_command()
        self._line_count = self.__get_line_count()

    def __setup_help_command(self):
        self._orig_help_command = self.ara.help_command
        self.ara.help_command = AraHelp(aliases=["halp", "h"], brief="Show this message")
        self.ara.help_command.cog = self

    def __get_ara_invite_link(self):
        params = urlencode(
            dict(
                client_id=self.ara.application_id,
                permissions=8 or 385088,
                scope=" ".join(["bot", "applications.commands"]),
            )
        )
        return f"https://discord.com/oauth2/authorize?{params}"

    def __get_line_count(self):
        count = 0
        try:
            for g in glob("arabot/**/*.py", recursive=True):
                with open(g, encoding="utf8") as f:
                    count += len(f.readlines())
        except OSError:
            return 0
        return count

    def __get_version(self):
        ver_str = f"{self.ara.name} v{arabot.__version__}"

        if not arabot.TESTING:
            return ver_str

        if commit_sha := getenv("HEROKU_SLUG_COMMIT") or getenv("RAILWAY_GIT_COMMIT_SHA"):
            dirty_indicator = ""
        else:
            try:
                commit_sha = check_output(["git", "rev-parse", "HEAD", "--"]).strip().decode()
                dirty_indicator = ".dirty" if check_output(["git", "status", "-s"]) else ""
            except (OSError, SubprocessError):
                return ver_str

        return f"{ver_str}+{commit_sha[:7]}{dirty_indicator}" if commit_sha else ver_str

    @command(aliases=["ver", "v"], brief="Show bot's version")
    async def version(self, ctx: Context):
        await self.ara.wait_until_ready()
        await ctx.send(utils.codeblock(self._version, "less"))

    @command(brief="Show bot's source code line count")
    async def lines(self, ctx: Context):
        if not self._line_count:
            await ctx.send("Couldn't read files")
            return
        await ctx.send(
            f"{ctx.ara.name} v{arabot.__version__} consists "
            f"of **{self._line_count}** lines of Python code"
        )

    @command(aliases=["github", "gh"], brief="Open bot's code repository")
    async def repo(self, ctx: Context):
        await ctx.send("<https://github.com/tooruu/AraBot>")

    @command(name="invite", brief="Show server's invite link")
    async def server_invite_link(self, ctx: Context):
        await ctx.send(await ctx.guild.get_unlimited_invite_link() or "Couldn't find invite link")

    @command(name="arabot", brief="Show bot's invite link")  # TODO: dynamically change name
    async def ara_invite_link(self, ctx: Context):
        await self.ara.wait_until_ready()
        await ctx.send(self._bot_invite_link)

    async def cog_load(self):
        await self.ara.wait_until_ready()
        self._version = self.__get_version()
        self._bot_invite_link = self.__get_ara_invite_link()

    def cog_unload(self):
        self.ara.help_command = self._orig_help_command


def setup(ara: Ara):
    ara.add_cog(Meta(ara))
