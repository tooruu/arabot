from random import choice, choices
from discord.ext.commands import command, Cog, cooldown, BucketType, CommandOnCooldown, MissingRequiredArgument, BadArgument
from json import load
from typing import Sequence
from math import isclose
from .._utils import bold

DATABASE_FILE_PATH = "./bot/res/database.json"
TABLE_ITEMS = "items"
TABLE_ITEM_TYPES = "item_types"
TABLE_ITEM_RANKS = "item_ranks"
TABLE_POOLS = "pools"
DROP_RATE_TOLERANCE = 1e-5
STIGMATA_PARTS = ("T", "M", "B")
STIGMATA_PARTS_FULL = tuple(f"({part})" for part in STIGMATA_PARTS)

class Gacha(Cog, name="Commands"):
	def __init__(self, client, database_file_path):
		self.bot = client
		self.gacha.cooldown_after_parsing = True
		with open(database_file_path) as database:
			self._database = load(database)
		self._pools = self.__load_pools()

	@cooldown(1, 60, BucketType.user)
	@command(aliases=["pull"], brief="<supply> [amount] | Try out your HI3 luck for free")
	async def gacha(self, ctx, supply_type: str, pull_count: int = 10):
		supply_type = supply_type.lower()
		supply = self._database.get(TABLE_POOLS, {}).get(supply_type)
		if supply is None or not supply.get("available", False):
			await ctx.send("The supply type you specified doesn't exist.")
			self.gacha.reset_cooldown(ctx)
			return
		pull_count = max(1, min(pull_count, 10))
		pulled_items = self.__pull_items(supply_type, pull_count)
		pulled_item_names = []
		for pulled_item in pulled_items:
			item = self.__get_item(pulled_item["id"])
			if item is None:
				pulled_item_names.append("Unknown item")
				continue
			item_name = pulled_item["name"]
			item_type = self._database.get(TABLE_ITEM_TYPES, {}).get(item.get("type", None))
			item_rank = self._database.get(TABLE_ITEM_RANKS, {}).get(item.get("rank", None))
			if item_type is not None and item_type.get("is_multi", False):
				count_min = item_type.get("multi_min", 1)
				count_max = item_type.get("multi_max", 1)
				item_name = f"{item_name} x{choice(range(count_min, count_max))}"
			elif item_rank is not None and item_rank.get("is_special", False):
				item_name = bold(item_name)
			pulled_item_names.append(item_name)
		await ctx.send("__**{}** supply drops:__\n{}".format(supply["name"], "\n".join(pulled_item_names)))

	@gacha.error
	async def on_error(self, ctx, error):
		if isinstance(error, CommandOnCooldown): # reset cd if command was invoked incorrectly
			return
		if isinstance(error, MissingRequiredArgument):
			await ctx.send(
				"__Currently available supplies:__\n" + "\n".join(
				[f"*{pool[0]}* - **{pool[1].get('name', 'Nameless Supply')}**" for pool in self.__get_available_pools()]
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

	def __get_item(self, item_id: str) -> dict:
		return self._database[TABLE_ITEMS].get(item_id)

	def __pull_items(self, supply_type: str, pull_count: int) -> Sequence[object]:
		supply = self._pools[supply_type]
		available_items = [item for item in supply]
		drop_rates = [item["rate"] for item in supply]
		return choices(available_items, drop_rates, k = pull_count)

	def __get_available_pools(self) -> Sequence[tuple]:
		for pool_id in self._pools.keys():
			pool_config = self._database.get(TABLE_POOLS, {}).get(pool_id, {})
			if pool_config.get("available", False):
				yield (pool_id, pool_config)

	def __load_pools(self):
		pools = {}
		item_configs = self._database.get(TABLE_ITEMS, {})
		item_type_configs = self._database.get(TABLE_ITEM_TYPES, {})
		for pool_type, pool_config in self._database.get(TABLE_POOLS, {}).items():
			pools[pool_type] = pool = []
			for loot_config in pool_config.get("loot_table", []):
				rate = loot_config.get("rate", 0.0)
				if isclose(rate, 0.0, rel_tol=DROP_RATE_TOLERANCE):
					print("Ignored loot table with 0.0 rate.")
					continue
				for item_id in loot_config.get("items", []):
					item_config = item_configs.get(item_id, None)
					if item_config is None:
						print(f"Warning! The item identified by '{item_id}' doesn't exist.")
						continue
					item_type_id = item_config.get("type", None)
					if item_type_id is None:
						print(f"Warning! The type of the item '{item_id}' isn't specified.")
						continue
					item_type_config = item_type_configs.get(item_type_id, None)
					if item_type_config is None:
						print(f"Warning! The item type identified by '{item_type_id}' doesn't exist.")
						continue
					item_name = item_config.get("name", "Unknown")
					if item_type_config.get("name", None) == "Stigmata" and not item_name.endswith(STIGMATA_PARTS_FULL):
						items_to_add = [f"{item_name} ({part})" for part in STIGMATA_PARTS]
					else:
						items_to_add = [item_name]
					pool.extend({
						"id": item_id,
						"name": item_to_add,
						"rate": rate
					} for item_to_add in items_to_add)
		return pools

def setup(client):
	client.add_cog(Gacha(client, DATABASE_FILE_PATH))