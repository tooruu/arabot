from discord.ext.commands import Bot
from os import walk
from os.path import basename
from cogs._utils import load_env


def load_ext(client):
	path = ""
	for root, _, files in walk("./bot/cogs"):
		if root[0] == "_":
			continue
		path += basename(root) + "."
		for cog in sorted(files):
			if cog.endswith(".py") and cog[0] != "_":
				client.load_extension(path + cog[:-3])
				print(f"Loaded {path}{cog[:-3]}")


if __name__ == "__main__":
	bot = Bot(command_prefix=";", case_insensitive=True)
	load_ext(bot)
	bot.run(load_env("token"))