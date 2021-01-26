from discord.ext.commands import command, Cog


class Sample(Cog, name="Commands"):
    def __init__(self, client):
        self.bot = client

    @command()
    async def sample(self, ctx):
        print("I'm a sample command")


def setup(client):
    client.add_cog(Sample(client))
