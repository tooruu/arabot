from random import choice, choices
from json import load
from typing import Sequence

# This file has a stupid name, because a certain someone .gitignored *test*
class Gacha:
	def __init__(self):
		with open("./bot/res/database.json") as database:
			self._database = load(database)
		self._pools = {}
		for supply_type, supply in self._database.get("pools", {}).items():
			self._pools[supply_type] = pool = []
			pool_total_rate = 0
			for loot_definition in supply.get("loot_table", []):
				for loot_item in loot_definition.get("items", []):
					pool.append({
						"id": loot_item,
						"rate": loot_definition.get("rate", 0)
					})
					pool_total_rate += loot_definition.get("rate", 0)
			print(f"Pool '{supply_type}' has {len(pool)} items and the total drop rate is {pool_total_rate}.")
		print(f"Total pool count is {len(self._pools)}.")

	def __get_item(self, item_id: str) -> dict:
		return self._database["items"].get(item_id)

	def __get_item_type(self, type_id: str) -> dict:
		return self._database["item_types"].get(type_id)

	def __pull_items(self, supply_type: str, pull_count: int) -> Sequence[str]:
		supply = self._pools[supply_type]
		available_items = [item["id"] for item in supply]
		drop_rates = [item["rate"] for item in supply]
		return choices(available_items, drop_rates, k = pull_count)

	def bigpull(self, supply_type: str, pull_count: int):
		return self.__pull_items(supply_type, pull_count)

	def gacha(self, supply_type: str, pull_count: int = 10):
		supply_type = supply_type.lower()
		supply = self._database["pools"].get(supply_type)
		if supply is None or not supply.get("available", False):
			print("The supply type you specified doesn't exist.")
			return
		pull_count = max(1, min(pull_count, 10))
		pulled_item_ids = self.__pull_items(supply_type, pull_count)
		pulled_item_names = []
		for pulled_item_id in pulled_item_ids:
			item = self.__get_item(pulled_item_id)
			item_name = item["name"] if item is not None else "Unknown item"
			item_type = self.__get_item_type(item.get("type", "0") if item is not None else 0)
			if item_type is not None and item_type.get("is_multi", False):
				count_min = item_type.get("multi_min", 1)
				count_max = item_type.get("multi_max", 1)
				item_name = f"{item_name} x{choice(range(count_min, count_max))}"
			elif item_type is not None and item_type.get("is_special", False):
				item_name = f"**{item_name}**"
			pulled_item_names.append(item_name)
		print("__**{}** supply drops:__\n{}".format(supply["name"], "\n".join(pulled_item_names)))

gacha = Gacha()
all_pulls = {}
for pull_index in range(1):
	items = gacha.bigpull("ex", 10)
	for item in items:
		if all_pulls.get(item) is None:
			all_pulls[item] = 0
		all_pulls[item] += 1
print(*["{}: {}".format(gacha._database["items"][pull[0]]["name"], pull[1]) for pull in all_pulls.items()], sep="\n")