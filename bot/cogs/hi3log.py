from discord.ext.commands import Cog
from discord.ext.tasks import loop
from aiohttp import ClientSession as WebSession
from re import match

class HI3Log(Cog):
	def __init__(self, client):
		self.bot = client
		self.old = ""
		self.new = ""

	@loop(hours=3)
	async def check(self):
		async with WebSession() as session:
			async with session.get("https://honkaiimpact3.gamepedia.com/api.php", params={
				"action": "parse",
				"page": "Update_Log",
				"section": 1,
				"format": "json",
				"prop": "wikitext"
			}) as response:
				try:
					self.new = (await response.json())["parse"]["wikitext"]["*"]
				except Exception as e:
					print(e)
		if self.new != self.old:
			await self.channel.send("Hey, Captain, {} patch is out!\nCheck out the changelog at <https://honkaiimpact3.gamepedia.com/Update_Log>".format(f"v{regex.group(1)}" if (regex:=match(r"==.+((?:\d\.){2}\d)==", self.new)) else "new"))
			self.old = self.new

	@Cog.listener()
	async def on_ready(self):
		self.channel = self.bot.get_channel(676894553545900047)
		self.check.start()

def setup(client):
	client.add_cog(HI3Log(client))