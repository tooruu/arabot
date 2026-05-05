import disnake
from disnake.ext import commands

from arabot.core import Ara, Category, Cog, Context, SettingKey
from arabot.core.database import Setting
from arabot.utils import bold, mono


class Settings(Cog, category=Category.SETTINGS):
    @commands.group(
        aliases=["set", "cfg", "config", "setting"], brief="Various bot settings", invoke_without_command=True
    )
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
        embed = disnake.Embed(description=ctx._("additional_prefix")).set_author(
            name=ctx.guild,
            icon_url=ctx.guild.icon,
        )

        if prefix:
            prefix = await Setting.set(SettingKey.PREFIX, prefix.strip(), ctx.guild.id)
        else:
            prefix = await Setting.get(SettingKey.PREFIX, ctx.guild.id) or ";"

        embed.title = f"{ctx._('title')}: {bold(mono(prefix))}"
        await ctx.send(embed=embed)

    @commands.has_permissions(manage_guild=True)
    @settings.command(
        brief="View or toggle russian roulette's kick setting",
        extras={"note": "Kicks after 3 consecutive losses"},
    )
    async def rrkick(self, ctx: Context, enabled: bool | None = None):
        embed = disnake.Embed().set_author(
            name=ctx.guild,
            icon_url=ctx.guild.icon and ctx.guild.icon.as_icon,
        )

        if enabled is None:
            enabled = await Setting.get(SettingKey.RR_KICK, ctx.guild.id)
        else:
            enabled = await Setting.set(SettingKey.RR_KICK, enabled, ctx.guild.id)

        embed.title = f"{ctx._('title')}: {'✅' if enabled else '❌'}"
        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Settings())
