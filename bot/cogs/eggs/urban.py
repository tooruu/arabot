from discord.ext.commands import Cog
from re import search

class EasterEggs(Cog):
	def __init__(self, client):
		self.bot = client

	@Cog.listener("on_message")
	async def urban_listener(self, msg):
		if regex := search(r"(wh?[ao]t(?:'?s|\sis)\s)(.[^?]+)", msg.content.lower()):
			if not (search(f"{regex.group(1)}(up|good|with|it|this|that|so|the)\\b", msg.content.lower()) or msg.content.startswith('>')):
				await self.bot.get_command("urban")(await self.bot.get_context(msg), term=regex.group(2))

def setup(client):
	client.add_cog(EasterEggs(client))