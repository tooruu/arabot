from discord.ext.commands import command, Cog
from .._utils import isDev

class Sample(Cog, name="Admin"):
	def __init__(self, client):
		self.bot = client

	@check(isDev)
	@command()
	async def sample(self, ctx):
		print("I'm a sample admin command")

def setup(client):
	client.add_cog(Sample(client))
