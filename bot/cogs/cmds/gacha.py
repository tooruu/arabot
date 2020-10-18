from random import choice, choices
from discord.ext.commands import command, Cog, cooldown, BucketType, CommandOnCooldown, MissingRequiredArgument, BadArgument
from json import load

class Gacha(Cog, name="Commands"):
	def __init__(self, client):
		self.bot = client
		self.gacha.cooldown_after_parsing = True
		with open("./bot/res/gacha.json") as gacha:
			self.pool = load(gacha)
		for supply in self.pool:
			for typ in self.pool[supply]["pool"]:
				if "Stig" in typ:
					self.pool[supply]["pool"][typ] = [
						stig if stig[-1] == ')' else f"{stig} ({slot})" for slot in ('T', 'M', 'B')
						for stig in self.pool[supply]["pool"][typ]
					]

	@cooldown(1, 60, BucketType.user)
	@command(aliases=["pull"], brief="<supply> [amount] | Try out your HI3 luck for free")
	async def gacha(self, ctx, supply, pulls: int = 10):
		if not self.pool.get(supply := supply.lower()) or not self.pool[supply]["available"]:
			await ctx.send("Invalid supply")
			self.gacha.reset_cooldown(ctx)
			return
		if pulls < 1:
			await ctx.send("Invalid amount")
			self.gacha.reset_cooldown(ctx)
			return
		pulls = min(pulls, 10)
		types = choices([*self.pool[supply]["rates"]], self.pool[supply]["rates"].values(), k=pulls)
		drops = []
		for typ in types:
			drop = choice(self.pool[supply]["pool"][typ])
			if "Frag" in typ:
				drop += f" {'soul' if drop in awk else 'fragment'} x{choice((5,6,7,8) if drop in awk else (4,5,6))}"
			if typ in ("ValkS+", "ValkS", "Weap4+", "Weap4", "Stig4+", "Stig4"):
				drop = f"**{drop}**"
			drops.append(drop)
		await ctx.send(
			"__**{}** supply drops:__\n{}".format(self.pool[supply].get("name") or supply.title(), "\n".join(drops))
		)

	@gacha.error
	async def on_error(self, ctx, error):
		if isinstance(error, CommandOnCooldown): # reset cd if command was invoked incorrectly
			return
		if isinstance(error, MissingRequiredArgument):
			await ctx.send(
				"__Currently available supplies:__\n" + "\n".join(
				[f"*{supply}* - **{self.pool[supply]['name']}**" for supply in self.pool if self.pool[supply]["available"]]
				)
			)
			return
		if isinstance(error, BadArgument):
			if repr(error) == "BadArgument('Converting to \"int\" failed for parameter \"pulls\".')":
				# im tired let me sleep
				await ctx.send(f"Cooldown expires in {self.gacha.get_cooldown_retry_after(ctx):.0f} seconds"
				if self.gacha.is_on_cooldown(ctx) else "Invalid amount")
				return
		self.gacha.reset_cooldown(ctx)
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
	"Herrscher of Thunder",
)

def setup(client):
	client.add_cog(Gacha(client))