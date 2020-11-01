from argparse import ArgumentParser
from json import dump, load

DATABASE_FILE_PATH = "./bot/res/database.json"
TABLE_ITEMS = "items"
TABLE_POOLS = "pools"

class GachaEditor:
	def __init__(self: GachaEditor):
		with open(DATABASE_FILE_PATH) as database:
			self._database = load(database)
			self._operations = {
				"listtables": self.__list_tables,

				# items
				"additem": self.__additem,
				"deleteitem": self.__deleteitem,
				"finditem": self.__finditem,

				# pools
				"addpool": self.__addpool,
				"removepool": self.__removepool,
				"addpoolitem": self.__addpoolitem,
				"removepoolitem": self.__removepoolitem
			}

	def __save_database(self: GachaEditor):
		with open(DATABASE_FILE_PATH, "w+") as database:
			dump(self._database, database)
		print("The database has been saved successfully.")

	def __get_or_initialize_table(self: GachaEditor, table_name: str) -> dict:
		table = self._database.get(table_name)
		if table is not None:
			return table
		table = self._database[table_name] = {}
		return table

	def __find_ids_by_field(self: GachaEditor, table_name: str, field_name: str, field_value: str):
		for key, item in self.__get_or_initialize_table(table_name).items():
			if item.get(field_name, "") == field_value:
				yield key

	# TODO Make the argument parser more obvious, because specifying the "names" argument here makes no sense.
	# python .\bot\tools\database_editor.py listtables all
	def __list_tables(self: GachaEditor, options):
		for table_id in self._database.keys():
			print(table_id)

	# database_editor.py --type 2 --rank 3 additem "name 1" "name 2"
	def __additem(self: GachaEditor, options):
		if not options.type:
			raise ValueError("The item type must be specified.")
		if not options.rank:
			raise ValueError("The item rank must be specified.")
		table = self.__get_or_initialize_table(TABLE_ITEMS)
		next_key = max((int(key) for key in table.keys()), default=0) + 1
		for item_index, item_name in enumerate(options.names):
			item_id = str(next_key + item_index)
			table[item_id] = {
				"name": item_name,
				"type": options.type,
				"rank": options.rank
			}
			print(f"Added item '{item_name}' with identifier '{item_id}'.")
		self.__save_database()

	# database_editor.py --field name finditem "name 1" "name 2"
	def __finditem(self: GachaEditor, options):
		if not options.field:
			raise ValueError("The field name must be specified.")
		table = self.__get_or_initialize_table(TABLE_ITEMS)
		for name in options.names:
			for item_id in self.__find_ids_by_field(TABLE_ITEMS, options.field, name):
				print(f"ID: {item_id}\nData: {table[item_id]}")

	# database_editor.py deleteitem "id 1" "id 2"
	# database_editor.py --field name deleteitem "name 1" "name 2"
	def __deleteitem(self: GachaEditor, options):
		table = self.__get_or_initialize_table(TABLE_ITEMS)
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

	# database_editor.py addpool <code> <name>
	# database_editor.py addpool ex "Expansion Battlesuit"
	def __addpool(self: GachaEditor, options):
		if len(options.names) < 2:
			raise ValueError("The code and the name must be specified. Eg. gacha_editor.py addpool ex \"Expansion Battlesuit\"")
		table = self.__get_or_initialize_table(TABLE_POOLS)
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
	def __removepool(self: GachaEditor, options):
		table = self.__get_or_initialize_table(TABLE_POOLS)
		has_changed = False
		for _, name in enumerate(options.names):
			if table.get(name) is None:
				print(f"The pool '{name}' does not exist.")
				continue
			table.pop(name)
			has_changed = True
			print(f"The pool '{name}' has been removed.'")
		if has_changed:
			self.__save_database()

	# database_editor.py addpoolitem --pool <code> --rate <drop rate> names [names]
	# database_editor.py addpoolitem -pool ex --rate 0.015 "ARC Serratus" "Blaze Destroyer"
	def __addpoolitem(self: GachaEditor, options):
		table = self.__get_or_initialize_table(TABLE_POOLS)
		print("Not implemented yet.")

	def __removepoolitem(self: GachaEditor, options):
		print("Not implemented yet.")

	def execute(self: GachaEditor, options):
		operation = self._operations.get(options.operation)
		if operation is not None:
			operation(options)
		else:
			print("Invalid operation.")

# python .\bot\tools\database_editor.py --operation find --table items --field name "ARC Serratus" "Valkyrie Bladestrike"
# python .\bot\tools\database_editor.py --operation add --table items --type 1 --rank 3 "ARC Serratus" "Blaze Destroyer" "Blooded Saints" "Dominators" "Energy Leapers" "Fafnir Flame" "Hallowed Saints" "Hurricanes" "Hyper Railguns" "Jingwei's Wings" "Judgement of Shamash" "Keys of the Void" "Light and Shadow" "Mjolnir" "PSY - Bows of Hel" "Proto Alberich's Bows" "Ranger's Pistol" "Shennong's Guardians" "Spirit Guns - Yae" "Thunder Kikaku" "Tranquil Arias" "Twins of Eden"
parser = ArgumentParser()
parser.add_argument("--type", dest="type", action="store", default="0")
parser.add_argument("--rank", dest="rank", action="store", default="0")
parser.add_argument("--field", dest="field", action="store", default=None)
parser.add_argument("--pool", dest="pool", action="store", default=None)
parser.add_argument("--rate", dest="rate", action="store", default=None)
parser.add_argument("operation", action="store")
parser.add_argument("names", nargs="+", action="store")
GachaEditor().execute(parser.parse_args())