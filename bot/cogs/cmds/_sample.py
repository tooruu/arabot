from discord.ext.commands import command, Cog

class Commands(Cog):
	def __init__(self, client):
		self.bot = client

	@command()
	async def sample(self, ctx):
		print("I'm a sample command")

def setup(client):
	client.add_cog(Commands(client))
