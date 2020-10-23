from discord.ext.commands import Cog
from .._utils import BOT_NAME, text_reaction
from re import match

class Chat(Cog, name="Eggs"):
	def __init__(self, client):
		self.bot = client

	@text_reaction(check=lambda msg: len(msg.content) < 20)
	def who(msg):
		return "ur mom"

	@text_reaction(regex=r"^(?:i(?:['’]?m|\sam)\s)+(?:(?:an?|the)\s)?(.+)", check=lambda msg: len(msg.content) < 30)
	def im_hi(msg):
		regex = match(r"(?:i(?:['’]?m|\sam)\s)+(?:(?:an?|the)\s)?(.+)", msg.content.lower())
		return f"hi {regex.group(1)}\nim {BOT_NAME}"

	@text_reaction(regex="\\brac(?:e|ing)\\b", cd=15)
	def racing(msg):
		return "***RACING TIME***", "🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽"

def setup(client):
	client.add_cog(Chat(client))
