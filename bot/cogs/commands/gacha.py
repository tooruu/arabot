from random import choice, choices
from discord.ext.commands import command, Cog, cooldown, BucketType, CommandOnCooldown, MissingRequiredArgument, BadArgument, ExpectedClosingQuoteError
from json import load

class Gacha(Cog):
	def __init__(self, client):
		self.bot = client
		with open("./bot/res/gacha_pool.json") as gacha:
			self.pool = {
				supply: {
				typ: [stig if stig[-1] == ')' else f"{stig} ({slot})" for slot in ('T', 'M', 'B')
				for stig in items] if "Stig" in typ else items
				for typ, items in pool.items()
				}
				for supply, pool in load(gacha).items()
			}
		with open("./bot/res/gacha_rates.json") as rates:
			self.rates = load(rates)
		self.gacha.cooldown_after_parsing = True

	@cooldown(1, 60, BucketType.user)
	@command(aliases=["pull"])
	async def gacha(self, ctx, supply, pulls: int = 10):
		if not self.pool.get(supply := supply.lower()):
			await ctx.send("Invalid supply")
			self.gacha.reset_cooldown(ctx)
			return
		if pulls < 1:
			await ctx.send("Invalid amount")
			self.gacha.reset_cooldown(ctx)
			return
		pulls = min(pulls, 10)
		types = choices([*self.rates[supply]], self.rates[supply].values(), k=pulls)
		drops = []
		for typ in types:
			drop = choice(self.pool[supply][typ])
			if "Frag" in typ:
				drop += f" {'soul' if drop in awk else 'fragment'} x{choice((5,6,7,8) if drop in awk else (4,5,6))}"
			if typ in ("ValkS+", "ValkS", "Weap4", "Stig4"):
				drop = f"**{drop}**"
			drops.append(drop)
		await ctx.send("__Your **{}** supply drops:__\n{}".format(supply.capitalize(), "\n".join(drops)))

	@gacha.error
	async def on_error(self, ctx, error):
		if isinstance(error, CommandOnCooldown): # reset cd if command was invoked incorrectly
			return
		if isinstance(error, MissingRequiredArgument):
			await ctx.send(
				"__The following supplies are available:__\n" +
				"\n".join([f"**{supply.capitalize()}**" for supply in self.rates])
			)
			return
		self.gacha.reset_cooldown(ctx)
		if isinstance(error, BadArgument):
			await ctx.send("Invalid amount") # assuming this exception can only happen with pull amount
			return
		raise error

awk = (
	"Goushinnso Memento",
	"Herrscher of Reason",
	"Ritual Imayoh",
	"Gyakushinn Miko",
	"Flame Sakitama",
	"Wolf's Dawn",
	"Luna Kindred",
	"Sixth Serenade",
	"Black Nucleus",
	"Sündenjäger",
	"Arctic Kriegsmesser",
	"Herrscher of the Void",
	"Vermillion Knight: Eclipse",
	"Azure Empyrea",
)

def setup(client):
	client.add_cog(Gacha(client))