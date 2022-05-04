from arabot.core import AnyTChl, Ara, Category, Cog, Context
from disnake.ext.commands import command, has_permissions


class Moderation(Cog, category=Category.MODERATION, command_attrs=dict(hidden=True)):
    def __init__(self, ara: Ara):
        self.ara = ara

    @command(aliases=["d"])
    @has_permissions(manage_messages=True)
    async def purge(self, ctx: Context, amount: int | None = None):
        if amount:
            await ctx.channel.purge(limit=amount + 1)
        else:
            await ctx.message.delete()

    @command()
    @has_permissions(manage_messages=True)
    async def csay(self, ctx: Context, chl: AnyTChl, *, msg: str):
        await ctx.message.delete()
        if chl:
            await chl.send(msg)


def setup(ara: Ara):
    ara.add_cog(Moderation(ara))
