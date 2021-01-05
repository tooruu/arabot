from .._item_resolver import ItemResolver
from .._utils import bold
from discord.ext.commands import Context, command, Cog, cooldown, BucketType, CommandOnCooldown, MissingRequiredArgument, BadArgument
from gacha.logging import ConsoleLog, LogLevel
from gacha.models.pulls import Pull
from gacha.persistence.json import JsonEntityProvider
from gacha.persistence.json.converters import ItemConverter, ItemRankConverter, ItemTypeConverter, PoolConverter
from gacha.providers import SimplePullProvider
from typing import Generator

DATABASE_FILE_PATH = "./bot/res/database.json"
LOG_LEVEL = LogLevel.WARNING

class Gacha(Cog, name="Commands"):
	def __init__(self, client):
		self.bot = client
		self.gacha.cooldown_after_parsing = True
		self._pull_provider = Gacha._initialize_pull_provider()

	@cooldown(1, 60, BucketType.user)
	@command(aliases=["pull"], brief="<supply> [amount] | Try out your HI3 luck for free")
	async def gacha(self, ctx: Context, supply_type: str, pull_count: int = 10):
		supply_type = supply_type.lower()
		if not self._pull_provider.has_pool(supply_type):
			await ctx.send(f"{ctx.author.mention}, the supply type you specified doesn't exist.")
			self.gacha.reset_cooldown(ctx)
			return
		pulls = self._pull_provider.pull(supply_type, pull_count)
		formatted_pulls = Gacha._format_pulls(pulls)
		await ctx.send("{},  here are your _{}_ supply drops:\n{}".format(
			ctx.author.mention,
			self._pull_provider.get_pool_name(supply_type),
			"\n".join(formatted_pulls)))

	@gacha.error
	async def on_error(self, ctx: Context, error):
		if isinstance(error, CommandOnCooldown):
			return
		if isinstance(error, MissingRequiredArgument):
			pools = [f"**{pool_code}** - {self._pull_provider.get_pool_name(pool_code)}" for pool_code in self._pull_provider.get_pool_codes()]
			await ctx.send(f"{ctx.author.mention}, currently available supplies:\n" + "\n".join(pools))
			return
		if isinstance(error, BadArgument):
			if repr(error) == "BadArgument('Converting to \"int\" failed for parameter \"pulls\".')":
				if self.gacha.is_on_cooldown(ctx):
					await ctx.send(f"{ctx.author.mention}, cooldown expires in {self.gacha.get_cooldown_retry_after(ctx):.0f} seconds.")
				else: ctx.send(f"{ctx.author.mention}, you specified an invalid amount.")
				return
		self.gacha.reset_cooldown(ctx)
		raise error

	@staticmethod
	def _initialize_pull_provider() -> SimplePullProvider:
		log = ConsoleLog(LOG_LEVEL)
		entity_provider = JsonEntityProvider(DATABASE_FILE_PATH, log, [
			ItemConverter(), ItemRankConverter(), ItemTypeConverter(), PoolConverter()
		])
		item_resolver = ItemResolver(entity_provider, log)
		return SimplePullProvider(entity_provider, item_resolver, log)

	@staticmethod
	def _format_pulls(pulls: Generator[Pull, None, None]) -> Generator[str, None, None]:
		for pull in pulls:
			formatted_pull = pull.name
			if pull.count > 1:
				formatted_pull = f"{formatted_pull} x{pull.count}"
			if pull.is_rare:
				formatted_pull = bold(formatted_pull)
			yield formatted_pull

def setup(client):
	client.add_cog(Gacha(client))