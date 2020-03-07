from discord.ext.commands import Bot
from os import walk, environ
from os.path import basename


def load_ext(client):
	path = ""
	for root, _, files in walk("./bot/cogs"):
		path += basename(root) + "."
		for cog in files:
			if cog.endswith(".py") and not cog.startswith("_"):
				client.load_extension(path + cog[:-3])
				print(f"Loaded {path}{cog[:-3]}")


if __name__ == "__main__":
	bot = Bot(command_prefix=";")
	try:
		token = environ["token"]
		bot.g_api_key = environ["g_api_key"]
		bot.g_cx = environ["g_cx"]
	except KeyError:
		with open("./secret") as s:
			token = s.readline()
			bot.g_api_key = s.readline()
			bot.g_cx = s.readline()
	load_ext(bot)
	bot.run(token)