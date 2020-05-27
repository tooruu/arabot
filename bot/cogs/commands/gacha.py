from random import choice, choices
from discord.ext.commands import command, Cog, cooldown, BucketType, CommandOnCooldown
from json import load

class Gacha(Cog):
	def __init__(self, client):
		self.bot = client
		with open("./bot/res/gacha_pool.json") as gacha:
			self.pool = {
				supply: {
				typ: [stig if '(' in stig else f"{stig} ({slot})" for slot in ('T', 'M', 'B')
				for stig in items] if "Stig" in typ else items
				for typ, items in pool.items()
				}
				for supply, pool in load(gacha).items()
			}
			print(self.pool)
		with open("./bot/res/gacha_rates.json") as rates:
			self.rates = load(rates)

	@cooldown(1, 60, BucketType.user)
	@command()
	async def gacha(self, ctx, supply="dorm", pulls: int = 10):
		if not self.pool.get(supply := supply.lower()):
			await ctx.send("Invalid supply")
			raise TypeError
		if pulls < 1:
			await ctx.send("Invalid amount")
			raise ValueError
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