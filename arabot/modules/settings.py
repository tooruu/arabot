import disnake
from arabot.core import Ara, AraDB, Category, Cog, Context
from arabot.utils import mono
from disnake.ext import commands


class Settings(Cog, category=Category.SETTINGS):
    @commands.group(aliases=["set"], invoke_without_command=True)
    async def settings(self, ctx: Context):
        pass

    @settings.command(brief="Show bot's prefix on this server")
    async def prefix(self, ctx: Context, prefix: str | None = None):
        db: AraDB = ctx.ara.db
        embed = disnake.Embed(title="Prefix").set_author(name=ctx.guild, icon_url=ctx.guild.icon)

        if prefix:
            await db.set_guild_prefix(ctx.guild.id, prefix)
            db.get_guild_prefix.invalidate(db, ctx.guild.id)
            embed.description = mono(prefix)
        else:
            prefix = await db.get_guild_prefix(ctx.guild.id)
            embed.description = mono(prefix or ";")

        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Settings())
