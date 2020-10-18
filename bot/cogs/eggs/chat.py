from discord.ext.commands import Cog
from .._utils import is_valid
from re import match

class Chat(Cog, name="Eggs"):
	def __init__(self, client):
		self.bot = client

	@Cog.listener("on_message")
	async def who(self, msg):
		if len(msg.content) < 20 and is_valid(self.bot, msg, "^who\\b"):
			await msg.channel.send("ur mom")

	@Cog.listener("on_message")
	async def im_hi(self, msg):
		if len(msg.content) < 30 and (regex := match(r"(?:i(?:['’]?m|\sam)\s)+(.+)", msg.content.lower())):
			await msg.channel.send(f"hi {regex.group(1)}\nim {BOT_NAME}")

	@Cog.listener("on_message")
	async def racing(self, msg):
		if is_valid(self.bot, msg, "\\brac(?:e|ing)\\b"):
			await msg.channel.send("***RACING TIME***")
			await msg.channel.send("🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽")

def setup(client):
	client.add_cog(Chat(client))
