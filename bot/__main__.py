from discord.ext.commands import Bot
from discord import Intents
from cogs._utils import BOT_PREFIX, load_ext, Help
from aiohttp import ClientSession as WebSession
from auth.credman import getenv

intents = Intents(
	guilds=True,
	members=True,
	emojis=True,
	voice_states=True,
	guild_messages=True,
	guild_reactions=True,
)

async def sessionify(client):
	client.ses = WebSession()

class TheBot(Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.loop.create_task(sessionify(self))

	async def close(self):
		await self.ses.close()
		await super().close()

if __name__ == "__main__":
	bot = TheBot(
		command_prefix=BOT_PREFIX,
		case_insensitive=True,
		intents=intents,
		#help_command=Help(),
	)
	load_ext(bot)
	bot.run(getenv("token"))