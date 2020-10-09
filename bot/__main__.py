from discord.ext.commands import Bot
from discord import Intents
from cogs._utils import getenv, BOT_PREFIX, load_ext
from aiohttp import ClientSession as WebSession

get_intents = lambda: Intents(
	guilds=True,
	members=True,
	emojis=True,
	voice_states=True,
	guild_messages=True
)

class TheBot(Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.ses = WebSession()

	async def close(self):
		await self.ses.close()
		await super().close()

if __name__ == "__main__":
	bot = TheBot(command_prefix=BOT_PREFIX, case_insensitive=True, intents=get_intents())
	load_ext(bot)
	bot.run(getenv("token"))