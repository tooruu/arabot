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


def load_env(client):
	if environ.get("token"):
		for k, v in environ.items():
			setattr(client, k, v)
			print("Assigned Bot." + k)
	else:
		with open("./.env") as s:
			for k, v in (line.split("=") for line in s.read().splitlines()):
				setattr(client, k, v)
				print("Assigned Bot." + k)


if __name__ == "__main__":
	bot = Bot(command_prefix=";")
	load_ext(bot)
	load_env(bot)
	bot.run(bot.token)