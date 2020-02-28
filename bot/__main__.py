from discord.ext.commands import Bot
from os import walk, environ


def load_cogs(client):
	path = ""
	for root, _, files in walk("./bot/cogs"):
		path += root.replace("\\", "/").split("/")[-1] + "." # because Windows sucks, and f-strings do too\
		for cog in files:
			if cog.endswith(".py") and not cog.startswith("_"):
				client.load_extension(path + cog[:-3])
				print(f"Loaded {path}{cog[:-3]}")


if __name__ == "__main__":
	try:
		token = environ["token"]
	except KeyError:
		with open("./secret") as s:
			token = s.read()
	bot = Bot(command_prefix=";")
	load_cogs(bot)
	bot.run(token)