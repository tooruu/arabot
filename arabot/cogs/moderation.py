from arabot.core import Ara, Cog, Context, Category
from arabot.utils import AnyTChl
from disnake.ext.commands import command, has_permissions


class Moderation(Cog, category=Category.MODERATION):
    def __init__(self, ara: Ara):
        self.ara = ara

    @command(aliases=["d"], hidden=True)
    @has_permissions(manage_messages=True)
    async def purge(self, ctx: Context, amount: int = None):
        if amount:
            await ctx.channel.purge(limit=amount + 1)
        else:
            await ctx.message.delete()

    @command(hidden=True)
    @has_permissions(manage_messages=True)
    async def csay(self, ctx: Context, chl: AnyTChl, *, msg):
        await ctx.message.delete()
        if chl:
            await chl.send(msg)


def setup(ara: Ara):
    ara.add_cog(Moderation(ara))
