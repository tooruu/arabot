from discord.ext.commands import Cog

class EasterEggs(Cog):
	def __init__(self, client):
		self.bot = client

	@Cog.listener("on_message")
	async def sample(self, msg):
		print("I'm a sample listener")

def setup(client):
	client.add_cog(EasterEggs(client))
