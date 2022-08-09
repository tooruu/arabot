import disnake
from arabot.core import Ara, AraDB, Category, Cog, Context
from arabot.utils import bold, mono
from disnake.ext import commands


class Settings(Cog, category=Category.SETTINGS):
    @commands.group(aliases=["set"], brief="Various bot settings", invoke_without_command=True)
    async def settings(self, ctx: Context):
        await ctx.send(
            embed=disnake.Embed().add_field(
                "Available settings",
                "\n".join(c.name for c in self.settings.walk_commands()),
            )
        )

    @commands.has_permissions(manage_guild=True)
    @settings.command(brief="View or set bot's prefix for this server")
    async def prefix(self, ctx: Context, prefix: str | None = None):
        db: AraDB = ctx.ara.db
        embed = disnake.Embed(
            description="_Additionally you can use **`ara`** or mention me_"
        ).set_author(name=ctx.guild, icon_url=ctx.guild.icon)

        if prefix:
            prefix = prefix.strip()
            await db.set_guild_prefix(ctx.guild.id, prefix)
            db.get_guild_prefix.invalidate(db, ctx.guild.id)
        else:
            prefix = await db.get_guild_prefix(ctx.guild.id) or ";"

        embed.title = f"Prefix: {bold(mono(prefix))}"
        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Settings())
