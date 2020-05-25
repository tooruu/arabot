from random import choice, choices
from discord.ext.commands import command, Cog, cooldown, BucketType, CommandOnCooldown
from json import load

class Gacha(Cog):
	def __init__(self, client):
		self.bot = client

	rates = {
		"ValkS": .015,
		"ValkA": .135,
		"ValkB": .055,
		"FragS": .0127,
		"FragA": .1019,
		"Weap4": .0046,
		"Weap3": .075,
		"Stig4": .0073,
		"Stig3": .225,
		"UpMats": .1474,
		"EquEXP": .1474,
		"Coins": .0737,
	}

	with open("./bot/res/gacha.json") as data:
		pool = load(data)

	@cooldown(1, 60, BucketType.user)
	@command()
	async def gacha(self, ctx, supply="dorm", pulls: int = 10):
		types = choices([*self.rates.keys()], self.rates.values(), k=pulls)
		drops = []
		for typ in types:
			drop = choice(self.pool[supply.lower()][typ])
			if "Stig" in typ and "(" not in drop:
				drop += f" ({choice(('T', 'M', 'B'))})"
			if typ in ("ValkS", "Weap4", "Stig4"):
				drop = f"**{drop}**"
			if "Frag" in typ:
				drop += f" frags x{choice((4,5,6))}"
			drops.append(drop)
		await ctx.send("__Your **{}** supply drops:__\n{}".format(supply.capitalize(), "\n".join(drops)))

	@gacha.error
	async def on_error(self, ctx, error):
		if isinstance(error, CommandOnCooldown): # reset cd if command was invoked incorrectly
			return
		self.gacha.reset_cooldown(ctx)
		raise error

def setup(client):
	client.add_cog(Gacha(client))