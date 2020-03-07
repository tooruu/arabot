from discord.ext.commands import Bot
from os import walk, environ
from os.path import basename


def load_ext(client):
	path = ""
	for root, _, files in walk("./bot/cogs"):
		path += basename(root) + "."
		for cog in sorted(files):
			if cog.endswith(".py") and cog[0] != ("_"):
				client.load_extension(path + cog[:-3])
				print(f"Loaded {path}{cog[:-3]}")


if __name__ == "__main__":
	bot = Bot(command_prefix=";")
	try:
		token = environ["token"]
		bot.g_api_key = environ["g_api_key"]
		bot.g_cx = environ["g_cx"]
	except KeyError:
		with open("./.env") as s:
			locals().update({line.partition("=")[0]: line.partition("=")[-1] for line in s.read().splitlines()})
		bot.g_api_key = g_api_key
		bot.g_cx = g_cx
	load_ext(bot)
	bot.run(token)