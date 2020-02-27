from discord.ext.commands import Bot
from os import walk


class AraBot(Bot):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	async def on_ready(self):
		# LOAD ALL COGS
		path = ""
		for root, _, files in walk("./bot/cogs"):
			root = root.replace("\\", "/")
			print(root, files)
			path += f"{root.split('/')[-1]}."
			print("new path is", path)
			for cog in files:
				if cog.endswith(".py") and not cog.startswith("_"):
					self.load_extension(path + cog[:-3])
					print(f"Loaded {path}{cog[:-3]}")
		#await setPresence(discord.ActivityType.watching, "#lewd")
		print("Ready!")


if __name__ == "__main__":
	try:
		import os
		token = os.environ["token"]
	except KeyError:
		with open("./secret") as s:
			token = s.read()
	AraBot(command_prefix=";").run(token)