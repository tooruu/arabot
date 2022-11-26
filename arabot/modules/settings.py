import disnake
from disnake.ext import commands

from arabot.core import Ara, AraDB, Category, Cog, Context
from arabot.utils import bold, mono


class Settings(Cog, category=Category.SETTINGS):
    @commands.group(aliases=["set"], brief="Various bot settings", invoke_without_command=True)
    async def settings(self, ctx: Context):
        await ctx.send(
            embed=disnake.Embed().add_field(
                ctx._("available_settings"),
                "\n".join(c.name for c in self.settings.walk_commands()),
            )
        )

    @commands.has_permissions(manage_guild=True)
    @settings.command(brief="View or set bot's prefix for this server")
    async def prefix(self, ctx: Context, prefix: str | None = None):
        db: AraDB = ctx.ara.db
        embed = disnake.Embed(description=ctx._("additional_prefix")).set_author(
            name=ctx.guild,
            icon_url=ctx.guild.icon and ctx.guild.icon.as_icon.compat,
        )

        if prefix:
            prefix = prefix.strip()
            await db.set_guild_prefix(ctx.guild.id, prefix)
        else:
            prefix = await db.get_guild_prefix(ctx.guild.id) or ";"

        embed.title = f"{ctx._('title')}: {bold(mono(prefix))}"
        await ctx.send(embed=embed)

    @commands.has_permissions(manage_guild=True)
    @settings.command(
        brief="View or toggle russian roulette's kick setting",
        extras={"note": "Kicks after 3 consecutive losses"},
    )
    async def rrkick(self, ctx: Context, enabled: bool | None = None):
        db: AraDB = ctx.ara.db
        embed = disnake.Embed().set_author(
            name=ctx.guild,
            icon_url=ctx.guild.icon and ctx.guild.icon.as_icon.compat,
        )

        if enabled is not None:
            await db.set_guild_rr_kick(ctx.guild.id, enabled)
        elif (enabled := await db.get_guild_prefix(ctx.guild.id)) is None:
            enabled = False

        embed.title = f"{ctx._('title')}: {'✅' if enabled else '❌'}"
        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Settings())
