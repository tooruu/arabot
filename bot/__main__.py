from discord.ext.commands import Bot
from discord import Intents
from os import walk
from os.path import basename
from cogs._utils import getenv, BOT_PREFIX

def load_ext(client):
	for path, _, files in walk("bot/cogs"):
		if basename(path := path[4:])[0] != "_":
			path = path.replace("/", ".").replace("\\", ".") + "."
			for cog in sorted(files):
				if cog[0] != "_" and cog.endswith(".py"):
					client.load_extension(path + cog[:-3])
					print(f"Loaded {path}{cog[:-3]}")

def get_intents():
	intents = Intents.default()
	intents.members = True
	intents.typing = False
	return intents

if __name__ == "__main__":
	bot = Bot(command_prefix=BOT_PREFIX, case_insensitive=True, intents=get_intents())
	load_ext(bot)
	bot.run(getenv("token"))