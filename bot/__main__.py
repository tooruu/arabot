from discord.ext.commands import Bot


class AraBot(Bot):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)


if __name__ == "__main__":
	try:
		import os
		token = os.environ["token"]
	except KeyError:
		with open("../secret") as s:
			token = s.read()
	bot = AraBot(command_prefix=";")
	bot.run(token)