from discord.ext.commands import command, Cog
from ...utils.meta import BOT_NAME, BOT_VERSION


class General(Cog, name="Admin"):
    def __init__(self, client):
        self.bot = client

    @command(aliases=["ver", "v"], brief="| Show currently running bot's version")
    async def version(self, ctx):
        await ctx.send(f"{BOT_NAME} v{BOT_VERSION}")


def setup(client):
    client.add_cog(General(client))
