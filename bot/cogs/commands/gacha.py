from random import choice, choices
from discord.ext.commands import command, Cog, cooldown, BucketType, CommandOnCooldown
from json import load

class Gacha(Cog):
	def __init__(self, client):
		self.bot = client
		with open("./bot/res/gacha_pool.json") as pool:
			self.pool = {
				typ: [stig if '(' in stig else f"{stig} ({slot})" for slot in ('T', 'M', 'B')
				for stig in items] if typ == "Stig4" else items
				for typ, items in load(pool).items()
			}
		with open("./bot/res/gacha_rates.json") as rates:
			self.rates = load(rates)

	@cooldown(1, 60, BucketType.user)
	@command()
	async def gacha(self, ctx, supply="dorm", pulls: int = 10):
		if not self.pool.get(supply := supply.lower()):
			await ctx.send("Invalid supply")
			return
		if pulls < 1:
			await ctx.send("Invalid amount")
			return
		pulls = min(pulls, 10)
		types = choices([*self.rates[supply]], self.rates[supply].values(), k=pulls)
		drops = []
		for typ in types:
			drop = choice(self.pool[supply][typ])
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