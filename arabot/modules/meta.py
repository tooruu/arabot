from collections.abc import Callable
from glob import glob
from itertools import groupby
from os import getenv
from subprocess import SubprocessError, check_output

import disnake
from disnake.ext import commands
from disnake.utils import utcnow

import arabot
from arabot.core import Ara, Category, Cog, Context
from arabot.utils import bold, codeblock, mono


class EmbedHelpCommand(commands.HelpCommand):
    def __init__(self, **command_attrs):
        super().__init__(command_attrs=command_attrs)

    async def prepare_help_command(self, ctx: commands.Context, command: str | None = None) -> None:
        bot: commands.Bot = ctx.bot
        self.embed = (
            disnake.Embed(timestamp=utcnow())
            .set_author(
                name=ctx._("help_menu").format(bot.name),
                icon_url=ctx.me.display_avatar.as_icon.compat,
            )
            .set_footer(text=f"{bot.name} v{arabot.__version__}")
        )

    async def send_bot_help(
        self, mapping: dict[commands.Cog | None, list[commands.Command]]
    ) -> None:
        bot: Ara = self.context.bot
        _: Callable[[str], str | None] = self.context._

        help_command_repr = self.context.clean_prefix + self.invoked_with
        self.embed.description = _("embed_description").format(help_command_repr)
        self.embed.set_thumbnail(url=bot.user.avatar.compat)

        get_category = self.get_command_category
        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        grouped = {cat: list(cmds) for cat, cmds in groupby(filtered, key=get_category)}
        sorted_ = sorted(grouped.items(), key=lambda group: sum(len(c.name) for c in group[1]))
        for category, cmds in sorted_:
            commands_field = ""
            for command in sorted(cmds, key=lambda c: c.name):
                command_repr = mono(command)
                if command.brief:
                    command_repr = f"[{command_repr}](http://. '{command.short_doc}')"
                if len(commands_field + command_repr) > 1024:
                    break
                commands_field += f"{command_repr} "
            self.embed.add_field(
                bold(_(category.name.lower())), commands_field[:-1] or _("no_commands")
            )
        await self.get_destination().send(embed=self.embed)

    async def send_command_help(self, command: commands.Command) -> None:
        self.fill_command_data(command)
        await self.get_destination().send(embed=self.embed)

    async def send_group_help(self, group: commands.Group) -> None:
        _ = self.context._
        self.fill_command_data(group)
        if subcmds := await self.filter_commands(group.commands, sort=True):
            self.embed.add_field(_("subcommands"), " ".join(mono(s.name) for s in subcmds))
        await self.get_destination().send(embed=self.embed)

    def fill_command_data(self, command: commands.Command) -> None:
        _ = self.context._
        self.embed.title = mono(command.name)
        self.embed.description = command.help or command.description or command.short_doc
        if note := command.extras.get("note"):
            self.embed.description += f"\n_{_('note')}: {note}_"
        if warning := command.extras.get("warning"):
            self.embed.description += f"\n_**{_('warning')}:** {warning}_"
        if command.aliases:
            self.embed.add_field(_("aliases"), " ".join(map(mono, sorted(command.aliases))))
        usage = f"{self.context.clean_prefix}{command} {command.signature}".rstrip()
        self.embed.add_field(
            _("usage"), mono(usage) + "\n" + self.get_usage_explanation(command), inline=False
        )

    def get_command_category(self, command: commands.Command) -> Category:
        return (
            command.extras.get("category")
            or getattr(command.cog, "category")
            or Category.NO_CATEGORY
        )

    def get_usage_explanation(self, command: commands.Command) -> str:
        _ = self.context._
        explanation = ""
        required = f"\n`<>` - {_('required')}"
        optional = f"\n`[]` - {_('optional')}"
        if command.usage is not None:
            if "<" in command.usage:
                explanation += required
            if "[" in command.usage:
                explanation += optional
        else:
            params = command.clean_params.values()
            if any(param.default is param.empty for param in params):
                explanation += required
            if any(param.default is not param.empty for param in params):
                explanation += optional
        if "=" in command.signature:
            explanation += f"\n`=` - {_('default')}"
        if "..." in command.signature:
            explanation += f"\n`...` - {_('variadic')}"
        return explanation


class Meta(Cog, category=Category.META):
    def __init__(self, ara: Ara):
        self.ara = ara
        self.__setup_help_command()
        self._line_count = self.__get_line_count()

    def __setup_help_command(self):
        self._orig_help_command = self.ara.help_command
        self.ara.help_command = EmbedHelpCommand(
            aliases=["halp", "h", "commands"], brief="Shows bot or command help"
        )
        self.ara.help_command.cog = self

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

    @commands.command(aliases=["ver", "v"], brief="Show bot's version")
    async def version(self, ctx: Context):
        await self.ara.wait_until_ready()
        await ctx.send(codeblock(self._version, lang="less"))

    @commands.command(brief="Show bot's source code line count")
    async def lines(self, ctx: Context):
        if not self._line_count:
            await ctx.send_("couldnt_read")
            return
        await ctx.send(
            ctx._("consists_of").format(f"{ctx.ara.name} v{arabot.__version__}", self._line_count)
        )

    @commands.command(aliases=["github", "gh"], brief="Link bot's code repository")
    async def repo(self, ctx: Context):
        await ctx.send("<https://github.com/tooruu/arabot>")

    @commands.command(name="invite", brief="Show server's invite link")
    async def server_invite_link(self, ctx: Context):
        await ctx.send(await ctx.guild.get_unlimited_invite_link() or ctx._("not_found", False))

    @commands.command(name="arabot", brief="Show bot's invite link")  # TODO:dynamically change name
    async def ara_invite_link(self, ctx: Context):
        await ctx.ara.wait_until_ready()
        await ctx.send(
            embed=disnake.Embed(title=ctx._("click_here"), url=self.ara.invite_url).set_author(
                name=ctx.ara.name,
                icon_url=ctx.ara.user.display_avatar.as_icon.compat,
                url=self.ara.invite_url,
            )
        )

    @commands.command(brief="Report a bug")
    async def bug(self, ctx: Context, *, description: str):
        reporter = ctx.author
        try:
            await ctx.ara.owner.send(
                embed=disnake.Embed(
                    title="Bug report", description=description, timestamp=utcnow()
                ).set_author(
                    name=reporter,
                    icon_url=reporter.avatar and reporter.avatar.as_icon.compat,
                    url=f"https://discord.com/users/{reporter.id}",
                )
            )
        except disnake.HTTPException:
            await ctx.reply(ctx._("contact_directly").format(ctx.ara.owner))
        else:
            await ctx.tick()

    async def cog_load(self):
        await self.ara.wait_until_ready()
        self._version = self.__get_version()

    def cog_unload(self):
        self.ara.help_command = self._orig_help_command


def setup(ara: Ara):
    ara.add_cog(Meta(ara))
