from discord.ext.commands import command, Cog, has_permissions


class Sample(Cog, name="Admin"):
    def __init__(self, client):
        self.bot = client

    @has_permissions(administrator=True)
    @command()
    async def sample(self, ctx):
        print("I'm a sample admin command")


def setup(client):
    client.add_cog(Sample(client))
