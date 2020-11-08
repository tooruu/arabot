from argparse import ArgumentParser
from json import dump, load
from math import isclose

DATABASE_FILE_PATH = "./bot/res/database.json"
TABLE_ITEMS = "items"
TABLE_POOLS = "pools"
DROP_RATE_TOLERANCE = 1e-5

# TODO LIST
# - fix the logic in gacha_teest.py and port it to gacha.py
# - smarter replacepoolitem
#   when you want to change a pool (typically due to banner updates)
#   you want to replace item sets, not just single items
#   so this command should take multiple item pairs as its arguments
#   like: "this" "to this" "this" "to this" "this" "to this"
# - togglepool
#   a command used to change the availability of a pool
# - smarter argparse
#   it sucks when you have to type unnecessary parameters
#   such as the listtables command
class GachaEditor:
	def __init__(self):
		with open(DATABASE_FILE_PATH) as database:
			self._database = load(database)
			self._operations = {
				# generic
				"listtables": self.__list_tables,

				# items
				"additem": self.__additem,
				"finditem": self.__finditem,
				"deleteitem": self.__deleteitem,
				"additemset": self.__additemset,

				# pools
				"addpool": self.__addpool,
				"removepool": self.__removepool,
				"addpoolitem": self.__addpoolitem,
				"removepoolitem": self.__removepoolitem,
				"replacepoolitem": self.__replacepoolitem,
				"showpool": self.__showpool
			}

	def __save_database(self):
		with open(DATABASE_FILE_PATH, "w+") as database:
			dump(self._database, database)
		print("The database has been saved successfully.")

	def __get_or_initialize_value(self, dictionary: dict, key: str, default_value: object) -> object:
		value = dictionary.get(key)
		if value is not None:
			return value
		dictionary[key] = value = default_value
		return value

	def __find_ids_by_field(self, table_name: str, field_name: str, field_value: str, is_exact: bool = True):
		predicate = (lambda text: text == field_value) if is_exact else (lambda text: field_value.lower() in text.lower())
		for key, item in self.__get_or_initialize_value(self._database, table_name, {}).items():
			if predicate(item.get(field_name, "")):
				yield key

	def __get_pool_total_rate(self, pool_code: str) -> float:
		table = self.__get_or_initialize_value(self._database, TABLE_POOLS, {})
		pool = table.get(pool_code)
		if pool is None:
			return 0.0
		loot_table = pool.get("loot_table", [])
		if len(loot_table) == 0:
			return 0.0
		total_rate = 0.0
		for _, descriptor in enumerate(loot_table):
			total_rate += descriptor.get("rate", 0.0) * len(descriptor.get("items", []))
		return total_rate

	def __validate_pool_total_rate(self, pool_code: str):
		total_rate = self.__get_pool_total_rate(pool_code)
		if not isclose(total_rate, 0.0, rel_tol=DROP_RATE_TOLERANCE) and not isclose(total_rate, 1.0, rel_tol=DROP_RATE_TOLERANCE):
			print(f"Warning! Pool '{pool_code}' has a total drop rate of {total_rate}.")

	# TODO Make the argument parser more obvious, because specifying the "names" argument here makes no sense.
	# python .\bot\tools\database_editor.py listtables all
	def __list_tables(self, options):
		"""Lists the names of the tables available in the database."""
		for table_id in self._database.keys():
			print(table_id)

	def __add_item_internal(self, item_name: str, item_type: str, item_rank: str = None, is_single_stigmata: bool = False) -> str:
		table = self.__get_or_initialize_value(self._database, TABLE_ITEMS, {})
		next_key = max((int(key) for key in table.keys()), default=0) + 1
		table[next_key] = item = {
			"name": item_name,
			"type": item_type
		}
		if item_rank is not None:
			item["rank"] = item_rank
		if is_single_stigmata:
			item["is_single_stigmata"] = True
		return next_key

	# database_editor.py --type <type> [--rank <rank>] additem "name 1" "name 2"
	# database_editor.py --type 2 --rank 3 additem "name 1" "name 2"
	def __additem(self, options):
		"""Adds a new item described by the specified options to the database."""
		if not options.type:
			raise ValueError("The item type must be specified.")
		for _, item_name in enumerate(options.names):
			item_id = self.__add_item_internal(item_name, options.type, options.rank, options.single)
			print(f"Added item '{item_name}' with identifier '{item_id}'.")
		self.__save_database()

	# database_editor.py --field name finditem "name 1" "name 2"
	def __finditem(self, options):
		if not options.field:
			raise ValueError("The field name must be specified.")
		table = self.__get_or_initialize_value(self._database, TABLE_ITEMS, {})
		for name in options.names:
			for item_id in self.__find_ids_by_field(TABLE_ITEMS, options.field, name, False):
				print(f"ID: {item_id}\nData: {table[item_id]}")

	# database_editor.py deleteitem "id 1" "id 2"
	# database_editor.py --field name deleteitem "name 1" "name 2"
	def __deleteitem(self, options):
		table = self.__get_or_initialize_value(self._database, TABLE_ITEMS, {})
		has_changed = False
		for _, name in enumerate(options.names):
			if not options.field and table.pop(name, None):
				has_changed = True
				print(f"Deleted item '{name}'.")
			elif options.field is not None:
				# Since we're using a generator function, we need to iterate through a list
				# different from the original dictionary to avoid concurrent modification.
				for item_id in list(self.__find_ids_by_field(TABLE_ITEMS, options.field, name)):
					table.pop(item_id)
					has_changed = True
					print(f"Deleted item '{item_id}'.")
		if has_changed:
			self.__save_database()

	# database_editor.py [--awakened] [--rank <rank>] additemset "Valkyrie" "Weapon" "Stigmata set"
	def __additemset(self, options):
		if len(options.names) != 3:
			raise ValueError("You must specify a valid itemset: valkyrie, weapon, stigmata.")
		def add_item(name, item_type, item_rank=None):
			item_id = self.__add_item_internal(name, item_type, item_rank)
			print(f"Added item '{name}' with identifier '{item_id}'.")
		add_item(options.names[0], "0", options.rank if options.rank is not None else "2")
		if options.awakened:
			add_item(f"{options.names[0]} soul", "2")
		else:
			add_item(f"{options.names[0]} fragment", "7")
		add_item(options.names[1], "1", "3")
		add_item(options.names[2], "8")
		self.__save_database()

	# database_editor.py addpool <code> <name>
	# database_editor.py addpool ex "Expansion Battlesuit"
	def __addpool(self, options):
		if len(options.names) < 2:
			raise ValueError("The code and the name must be specified. Eg. gacha_editor.py addpool ex \"Expansion Battlesuit\"")
		table = self.__get_or_initialize_value(self._database, TABLE_POOLS, {})
		if table.get(options.names[0]) is not None:
			raise ValueError("The specified pool already exists.")
		table[options.names[0]] = {
			"name": options.names[1],
			"available": True,
			"loot_table": []
		}
		self.__save_database()

	# database_editor.py removepool <code> <code> <code>
	# database_editor.py removepool ex foca focb
	def __removepool(self, options):
		table = self.__get_or_initialize_value(self._database, TABLE_POOLS, {})
		has_changed = False
		for _, name in enumerate(options.names):
			if table.get(name) is None:
				print(f"The pool '{name}' doesn't exist.")
				continue
			table.pop(name)
			has_changed = True
			print(f"The pool '{name}' has been removed.'")
		if has_changed:
			self.__save_database()

	# database_editor.py -pool <code> --rate <drop rate> addpoolitem names [names]
	# database_editor.py --pool ex --rate 0.015 addpoolitem "ARC Serratus" "Blaze Destroyer"
	def __addpoolitem(self, options):
		rate = float(options.rate)
		if rate < 0.0 or rate > 1.0:
			raise ValueError("The drop rate must be between 0.0, inclusive and 1.0, inclusive.")
		table = self.__get_or_initialize_value(self._database, TABLE_POOLS, {})
		pool = table.get(options.pool)
		if pool is None:
			raise ValueError("The specified pool doesn't exist.")
		loot_table = self.__get_or_initialize_value(pool, "loot_table", [])
		matching_descriptor = None
		for descriptor in loot_table:
			# Since it's impossible to precisely compare two floating-point numbers,
			# we use a relative tolerance to check for equality.
			if not isclose(descriptor.get("rate", 0.0), rate, rel_tol=DROP_RATE_TOLERANCE):
				continue
			matching_descriptor = descriptor
			break
		has_changed = False
		if matching_descriptor is None:
			matching_descriptor = {
				"rate": rate,
				"items": []
			}
			loot_table.append(matching_descriptor)
			has_changed = True
		item_list = matching_descriptor.get("items")
		if item_list is None:
			matching_descriptor["items"] = item_list = []
		for _, name in enumerate(options.names):
			item_id = next(self.__find_ids_by_field(TABLE_ITEMS, "name", name), -1)
			if item_id == -1:
				print(f"Item '{name}' doesn't exist, hence it won't be added to the pool.")
				continue
			if item_id in item_list:
				print(f"Item '{name}' is already added to the pool with the same rate, hence it won't be added again.")
				continue
			for descriptor_index, descriptor in enumerate(loot_table):
				other_item_list = descriptor.get("items", [])
				if item_id in other_item_list:
					other_item_list.remove(item_id)
					print(f"Item '{name}' has been removed with drop rate {descriptor.get('rate', 0.0)}.")
					if len(other_item_list) == 0:
						loot_table.pop(descriptor_index)
					break
			item_list.append(item_id)
			has_changed = True
			print(f"Added item '{name}' to the pool with drop rate {rate}.")
		print(f"There are currently {len(item_list)} items in the pool '{options.pool}' with rate {rate}.")
		self.__validate_pool_total_rate(options.pool)
		if has_changed and len(item_list) > 0:
			self.__save_database()

	# database_editor.py --pool <code> removepoolitem names [names]
	# database_editor.py --pool ex removepoolitem "ARC Serratus" "Blaze Destroyer"
	def __removepoolitem(self, options):
		table = self.__get_or_initialize_value(self._database, TABLE_POOLS, {})
		pool = table.get(options.pool)
		if pool is None:
			raise ValueError("The specified pool doesn't exist.")
		loot_table = self.__get_or_initialize_value(pool, "loot_table", [])
		has_changed = False
		for _, name in enumerate(options.names):
			item_id = next(self.__find_ids_by_field(TABLE_ITEMS, "name", name), -1)
			if item_id == -1:
				print(f"Item '{name}' doesn't exist, hence it won't be added to the pool.")
				continue
			is_found = False
			for descriptor_index, descriptor in enumerate(loot_table):
				item_list = descriptor.get("items", [])
				if item_id in item_list:
					item_list.remove(item_id)
					print(f"Item '{name}' has been removed.")
					if len(item_list) == 0:
						loot_table.pop(descriptor_index)
					is_found = True
					has_changed = True
					break
			if not is_found:
				print(f"Item '{name}' isn't in the pool, hence it won't be removed.")
		self.__validate_pool_total_rate(options.pool)
		if has_changed:
			self.__save_database()

	# database_editor.py --pool <code> replacepoolitem <name 1> <name 2>
	# database_editor.py --pool ex replacepoolitem "Stygian Nymph" "Bright Knight: Excelsis"
	def __replacepoolitem(self, options):
		if len(options.names) < 2:
			raise ValueError("Both the name of the item to be replaced and the item replacing it must be specified.")
		table = self.__get_or_initialize_value(self._database, TABLE_POOLS, {})
		pool = table.get(options.pool)
		if pool is None:
			raise ValueError("The specified pool doesn't exist.")
		loot_table = self.__get_or_initialize_value(pool, "loot_table", [])
		old_item_name = options.names[0]
		new_item_name = options.names[1]
		old_item_id = next(self.__find_ids_by_field(TABLE_ITEMS, "name", old_item_name), None)
		new_item_id = next(self.__find_ids_by_field(TABLE_ITEMS, "name", new_item_name), None)
		if old_item_id is None:
			raise ValueError(f"The item '{old_item_name}' doesn't exist.")
		if new_item_id is None:
			raise ValueError(f"The item '{new_item_name}' doesn't exist.")
		for _, descriptor in enumerate(loot_table):
			item_list = descriptor.get("items", [])
			if old_item_id in item_list:
				item_list.remove(old_item_id)
				item_list.append(new_item_id)
				print(f"The item '{old_item_name}' has been replaced by the item '{new_item_name}'.")
				self.__save_database()
				return
		print(f"The item '{old_item_name}' cannot be found in the pool.")

	# database_editor.py showpool <code>
	# database_editor.py showpool ex
	def __showpool(self, options):
		pools = self.__get_or_initialize_value(self._database, TABLE_POOLS, {})
		pool = pools.get(options.names[0], None)
		if pool is None:
			raise ValueError(f"The pool '{options.names[0]}' doesn't exist.")
		items = self.__get_or_initialize_value(self._database, TABLE_ITEMS, {})
		loot_table = pool.get("loot_table", [])
		for descriptor in loot_table:
			rate = descriptor.get("rate", 0)
			item_ids = descriptor.get("items", [])
			item_names = []
			for item_id in item_ids:
				item_names.append(items.get(item_id, {}).get("name", "Unknown item"))
			print("Rate '{}': {}".format(rate, ", ".join(item_names)))

	def execute(self, options):
		operation = self._operations.get(options.operation)
		if operation is not None:
			print(f"Invoking operation '{options.operation}'...")
			operation(options)
			print(f"Operation '{options.operation}' finished.")
		else:
			print(f"Invalid operation '{options.operation}'.")

parser = ArgumentParser()
parser.add_argument("--type", default="0") # Item type
parser.add_argument("--rank", default=None) # Item rank
parser.add_argument("--single", action="store_const", const=True) # Is single (non-set) stigmata?
parser.add_argument("--awakened", action="store_const", const=True) # Is awakened valkyrie?
parser.add_argument("--field", default=None) # Field name
parser.add_argument("--pool", default=None) # Pool ID
parser.add_argument("--rate",  default=None) # Drop rate
parser.add_argument("operation") # Operation to perform
parser.add_argument("names", nargs="+")
GachaEditor().execute(parser.parse_args())