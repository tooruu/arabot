from discord.ext.commands import Bot
from os import walk, environ


def load_cogs(client):
	path = ""
	for root, _, files in walk("./bot/cogs"):
		root = root.replace("\\", "/") # because Windows sucks, and f-strings too\
		path += f"{root.split('/')[-1]}."
		for cog in files:
			if cog.endswith(".py") and not cog.startswith("_"):
				client.load_extension(path + cog[:-3])
				print(f"Loaded {path}{cog[:-3]}")


class AraBot(Bot):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)


if __name__ == "__main__":
	try:
		token = environ["token"]
	except KeyError:
		with open("./secret") as s:
			token = s.read()
	bot = AraBot(command_prefix=";")
	load_cogs(bot)
	bot.run(token)