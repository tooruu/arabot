from discord.ext.commands import Cog
from re import search
from .._utils import is_valid

class Urban(Cog, name="Eggs"):
	def __init__(self, client):
		self.bot = client

	@Cog.listener("on_message")
	async def urban_listener(self, msg):
		regex = r"^(?:wh?[ao]t(?:['’]?s|\sis)\s)((?:(?!up|good|with|it|this|that|so|the|about|goin|happenin).)*?)\??$"
		if len(msg.content) < 30 and is_valid(self.bot, msg, regex):
			term = search(regex, msg.content.lower()).group(1)
			await self.bot.get_command("urban")(await self.bot.get_context(msg), term=term)

def setup(client):
	client.add_cog(Urban(client))