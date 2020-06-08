from discord.ext.commands import Bot
from os import walk
from os.path import basename
from cogs._utils import load_env

def load_ext(client):
	for path, _, files in walk("bot/cogs"):
		if basename(path := path[4:])[0] != "_":
			path = path.replace("/", ".").replace("\\", ".") + "."
			for cog in sorted(files):
				if cog[0] != "_" and cog.endswith(".py"):
					client.load_extension(path + cog[:-3])
					print(f"Loaded {path}{cog[:-3]}")

if __name__ == "__main__":
	bot = Bot(command_prefix=";", case_insensitive=True)
	load_ext(bot)
	bot.run(load_env("token"))