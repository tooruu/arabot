from copy import deepcopy
from math import isclose
from typing import Any, Callable, Dict, Iterable, TypeVar

TABLE_ITEMS = "items"
TABLE_ITEM_TYPES = "item_types"
TABLE_POOLS = "pools"
DROP_RATE_TOLERANCE = 1e-5
STIGMATA_PARTS = ("T", "M", "B")
STIGMATA_PARTS_FULL = tuple(f"({part})" for part in STIGMATA_PARTS)

_T = TypeVar("_T")
_T2 = TypeVar("_T2")


class DatabaseEditor:
    def __init__(self, database: Dict[str, Any]):
        self.database = database
        self.logs_enabled = True

    # TODO Make the argument parser more obvious, because specifying the "names" argument here makes no sense.
    # python tools/database_editor.py listtables all
    def list_tables(self, options) -> bool:
        """Lists the names of the tables available in the database."""
        for table_id in self.database.keys():
            self._log(table_id)
        return False

    # database_editor.py --type <type> [--rank <rank>] additem "name 1" "name 2"
    # database_editor.py --type 2 --rank 3 additem "name 1" "name 2"
    def add_item(self, options):
        """Adds a new item described by the specified options to the database."""
        if not options.type:
            raise ValueError("The item type must be specified.")
        if len(options.names) == 0:
            return False
        for item_name in options.names:
            item_id = self._add_item_internal(item_name, options.type, options.rank, options.single)
            self._log(f"Added item '{item_name}' with identifier '{item_id}'.")
        return True

    # database_editor.py --field name finditem "name 1" "name 2"
    def find_item(self, options) -> bool:
        if not options.field:
            raise ValueError("The field name must be specified.")
        table = self.database.setdefault(TABLE_ITEMS, {})
        for name in options.names:
            for item_id in self._find_ids_by_field(TABLE_ITEMS, options.field, name, False):
                self._log(f"ID: {item_id}\nData: {table[item_id]}")
        return False

    # database_editor.py deleteitem "id 1" "id 2"
    # database_editor.py --field name deleteitem "name 1" "name 2"
    def delete_item(self, options) -> bool:
        table = self.database.setdefault(TABLE_ITEMS, {})
        has_changed = False
        for name in options.names:
            if not options.field and table.pop(name, None):
                has_changed = True
                self._log(f"Deleted item '{name}'.")
            elif options.field is not None:
                # Since we're using a generator function, we need to iterate through a list
                # different from the original dictionary to avoid concurrent modification.
                for item_id in list(self._find_ids_by_field(TABLE_ITEMS, options.field, name)):
                    table.pop(item_id)
                    has_changed = True
                    self._log(f"Deleted item '{item_id}'.")
        return has_changed

    # database_editor.py [--awakened] [--rank <rank>] additemset "Valkyrie" "Weapon" "Stigmata set"
    def add_item_set(self, options) -> bool:
        if len(options.names) != 3:
            raise ValueError("You must specify a valid itemset: valkyrie, weapon, stigmata.")

        def add_item(name, item_type, item_rank=None):
            item_id = self._add_item_internal(name, item_type, item_rank)
            self._log(f"Added item '{name}' with identifier '{item_id}'.")

        add_item(options.names[0], "0", options.rank if options.rank is not None else "2")
        if options.awakened:
            add_item(f"{options.names[0]} soul", "2")
        else:
            add_item(f"{options.names[0]} fragment", "7")
        add_item(options.names[1], "1", "3")
        add_item(options.names[2], "8", options.rank if options.rank is not None else "2")
        return True

    # database_editor.py addpool <code> <name>
    # database_editor.py addpool ex "Expansion Battlesuit"
    def add_pool(self, options) -> bool:
        if len(options.names) < 2:
            raise ValueError(
                'The code and the name must be specified. Eg. gacha_editor.py addpool ex "Expansion Battlesuit"'
            )
        table = self.database.setdefault(TABLE_POOLS, {})
        if table.get(options.names[0]) is not None:
            raise ValueError("The specified pool already exists.")
        table[self._get_next_id(TABLE_POOLS)] = {
            "name": options.names[1],
            "code": options.names[0],
            "available": True,
            "loot_table": [],
        }
        return True

    # database_editor.py removepool <code> <code> <code>
    # database_editor.py removepool ex foca focb
    def remove_pool(self, options) -> bool:
        table = self.database.setdefault(TABLE_POOLS, {})
        has_changed = False
        for name in options.names:
            pool_id = self._find_id_by_field(TABLE_POOLS, "code", name)
            if pool_id is None:
                self._log(f"The pool '{name}' doesn't exist.")
                continue
            table.pop(pool_id)
            has_changed = True
            self._log(f"The pool '{name}' has been removed.")
        return has_changed

    # database_editor.py -pool <code> --rate <drop rate> addpoolitem names [names]
    # database_editor.py --pool ex --rate 0.015 addpoolitem "ARC Serratus" "Blaze Destroyer"
    def add_pool_item(self, options) -> bool:
        rate = float(options.rate)
        if rate < 0.0 or rate > 1.0:
            raise ValueError("The drop rate must be between 0.0, inclusive and 1.0, inclusive.")
        table = self.database.setdefault(TABLE_POOLS, {})
        pool_id = self._find_id_by_field(TABLE_POOLS, "code", options.pool)
        pool = table.get(pool_id)
        if pool is None:
            raise ValueError("The specified pool doesn't exist.")
        loot_table = pool.setdefault("loot_table", [])
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
            matching_descriptor = {"rate": rate, "items": []}
            loot_table.append(matching_descriptor)
            has_changed = True
        item_list = matching_descriptor.get("items")
        if item_list is None:
            matching_descriptor["items"] = item_list = []
        for name in options.names:
            item_id = self._find_item_id(name)
            if item_id is None:
                self._log(f"Item '{name}' doesn't exist, hence it won't be added to the pool.")
                continue
            if item_id in item_list:
                self._log(
                    f"Item '{name}' is already added to the pool with the same rate, hence it won't be added again."
                )
                continue
            for descriptor_index, descriptor in enumerate(loot_table):
                other_item_list = descriptor.get("items", [])
                if item_id in other_item_list:
                    other_item_list.remove(item_id)
                    self._log(
                        f"Item '{name}' has been removed with drop rate {descriptor.get('rate', 0.0)}."
                    )
                    if len(other_item_list) == 0:
                        loot_table.pop(descriptor_index)
                    break
            item_list.append(item_id)
            has_changed = True
            self._log(f"Added item '{name}' to the pool with drop rate {rate}.")
        self._log(
            f"There are currently {len(item_list)} items in the pool '{options.pool}' with rate {rate}."
        )
        self._validate_pool_total_rate(options.pool)
        return has_changed and len(item_list) > 0

    # database_editor.py --pool <code> removepoolitem names [names]
    # database_editor.py --pool ex removepoolitem "ARC Serratus" "Blaze Destroyer"
    def remove_pool_item(self, options) -> bool:
        table = self.database.setdefault(TABLE_POOLS, {})
        pool_id = self._find_id_by_field(TABLE_POOLS, "code", options.pool)
        pool = table.get(pool_id)
        if pool is None:
            raise ValueError("The specified pool doesn't exist.")
        loot_table = pool.setdefault("loot_table", [])
        has_changed = False
        for name in options.names:
            item_id = self._find_item_id(name)
            if item_id is None:
                self._log(f"Item '{name}' doesn't exist, hence it won't be added to the pool.")
                continue
            is_found = False
            for descriptor_index, descriptor in enumerate(loot_table):
                item_list = descriptor.get("items", [])
                if item_id in item_list:
                    item_list.remove(item_id)
                    self._log(f"Item '{name}' has been removed.")
                    if len(item_list) == 0:
                        loot_table.pop(descriptor_index)
                    is_found = True
                    has_changed = True
                    break
            if not is_found:
                self._log(f"Item '{name}' isn't in the pool, hence it won't be removed.")
        self._validate_pool_total_rate(options.pool)
        return has_changed

    # database_editor.py --pool <code> [--fragments] replacepoolitem <name 1> <name 2> [<name 1> <name 2> ...]
    # database_editor.py --pool ex replacepoolitem "Stygian Nymph" "Bright Knight: Excelsis"
    def replace_pool_item(self, options) -> bool:
        if len(options.names) % 2 != 0:
            raise ValueError("You must specify name pairs.")
        pools = self.database.setdefault(TABLE_POOLS, {})
        pool_id = self._find_id_by_field(TABLE_POOLS, "code", options.pool)
        pool = pools.get(pool_id)
        if pool is None:
            raise ValueError("The specified pool doesn't exist.")
        loot_table = pool.setdefault("loot_table", [])
        has_changed = False
        for old_item_name, new_item_name in zip(options.names[::2], options.names[1::2]):
            if not self._replace_pool_item(loot_table, old_item_name, new_item_name):
                continue
            has_changed = True
            if options.fragments:
                self._replace_pool_valkyrie_fragment(loot_table, old_item_name, new_item_name)
        return has_changed

    # database_editor.py showpool <code>
    # database_editor.py showpool ex
    def show_pool(self, options) -> bool:
        pools = self.database.setdefault(TABLE_POOLS, {})
        pool_id = self._find_id_by_field(TABLE_POOLS, "code", options.names[0])
        pool = pools.get(pool_id, None)
        if pool is None:
            raise ValueError(f"The pool '{options.names[0]}' doesn't exist.")
        items = self.database.setdefault(TABLE_ITEMS, {})
        for descriptor in pool.get("loot_table", []):
            rate = descriptor.get("rate", 0.0)
            item_names = []
            for item_id in descriptor.get("items", []):
                item = items.get(item_id, {})
                item_names.append(item.get("name", "Unknown item"))
            self._log(f"Rate '{rate}': {', '.join(item_names)}")
        self._log(f"Total drop rate is '{self._get_pool_total_rate(options.names[0])}'.")
        return False

    # database_editor.py togglepool <code>
    # database_editor.py togglepool ex
    def toggle_pool(self, options) -> bool:
        pools = self.database.setdefault(TABLE_POOLS, {})
        pool_id = self._find_id_by_field(TABLE_POOLS, "code", options.names[0])
        pool = pools.get(pool_id, None)
        if pool is None:
            raise ValueError(f"The pool '{options.names[0]}' doesn't exist.")
        pool["available"] = new_status = not pool.get("available", False)
        self._log(f"Pool '{options.names[0]}' is now {'' if new_status else 'un'}available.")
        return True

    # database_editor.py clonepool foca focb "Focused Supply B"
    def clone_pool(self, options) -> bool:
        if len(options.names) != 3:
            raise ValueError(
                "You must specify the source and the target pool identifiers, and the target pool name."
            )
        pools = self.database.setdefault(TABLE_POOLS, {})
        pool_id = self._find_id_by_field(TABLE_POOLS, "code", options.names[0])
        pool = pools.get(pool_id)
        if pool is None:
            raise ValueError("The pool with the specified identifier doesn't exist.")
        new_pool = deepcopy(pool)
        new_pool["name"] = options.names[2]
        new_pool["code"] = options.names[1]
        new_pool_id = self._get_next_id(TABLE_POOLS)
        self.database[TABLE_POOLS][new_pool_id] = new_pool
        self._log(
            f"Pool '{options.names[1]}' has been created with the identifier '{new_pool_id}'."
        )
        return True

    @staticmethod
    def _aggregate(source: Iterable[_T], seed: _T2, func: Callable[[_T2, _T], _T2]) -> _T2:
        current_value = seed
        for item in source:
            current_value = func(current_value, item)
        return current_value

    def _get_next_id(self, table_name: str) -> int:
        table = self.database.get(table_name, None)
        if table is None:
            return 1
        return max((int(key) for key in table.keys()), default=0) + 1

    def _get_pool_total_rate(self, pool_code: str) -> float:
        """
        Calculates the total drop rate for the items in the loot table
        of the pool identified by the specified ``pool_code``.

        This function accounts for stigmatas, too.
        """
        table = self.database.setdefault(TABLE_POOLS, {})
        pool_id = self._find_id_by_field(TABLE_POOLS, "code", pool_code)
        pool = table.get(pool_id)
        if pool is None:
            return 0.0
        loot_table = pool.get("loot_table", [])
        if len(loot_table) == 0:
            return 0.0
        return DatabaseEditor._aggregate(loot_table, 0.0, lambda c, i: c + i.get("rate", 0.0))

    def _find_ids_by_field(
        self, table_name: str, field_name: str, field_value: str, is_exact: bool = True
    ):
        """
        Finds all the identifiers in the table with the specified ``table_name``
        whose fields identified by the specified ``field_name``
        match the specified ``field_value``.
        If ``is_exact`` is set to ``True``, only exact matches are returned.
        """
        predicate = (
            (lambda text: text == field_value)
            if is_exact
            else (lambda text: field_value.casefold() in text.casefold())
        )
        for key, item in self.database.setdefault(table_name, {}).items():
            if predicate(item.get(field_name, "")):
                yield key

    def _find_id_by_field(
        self,
        table_name: str,
        field_name: str,
        field_value: str,
        is_exact: bool = True,
        default_value=None,
    ):
        return next(
            self._find_ids_by_field(table_name, field_name, field_value, is_exact),
            default_value,
        )

    def _find_item_id(self, item_name: str) -> str:
        """Finds the unique identifier of the item with the specified name."""
        return next(self._find_ids_by_field(TABLE_ITEMS, "name", item_name), None)

    def _find_valkyrie_fragment_id(self, valkyrie_name: str) -> str:
        """Finds the unique identifier of fragment/soul that belongs to the Valkyrie with the specified name."""
        # TODO Mark valkyries with "is_awakened": True so it's easier to find the matching frag/soul.
        return self._find_item_id(f"{valkyrie_name} fragment") or self._find_item_id(
            f"{valkyrie_name} soul"
        )

    def _validate_pool_total_rate(self, pool_code: str):
        """
        Validates the total drop rate of the pool identified by the specified ``pool_code``.
        """
        total_rate = self._get_pool_total_rate(pool_code)
        if not isclose(total_rate, 0.0, rel_tol=DROP_RATE_TOLERANCE) and not isclose(
            total_rate, 1.0, rel_tol=DROP_RATE_TOLERANCE
        ):
            self._log(f"Warning! Pool '{pool_code}' has a total drop rate of {total_rate}.")

    def _add_item_internal(
        self,
        item_name: str,
        item_type: str,
        item_rank: str = None,
        is_single_stigmata: bool = False,
    ) -> str:
        table = self.database.setdefault(TABLE_ITEMS, {})
        next_key = self._get_next_id(TABLE_ITEMS)
        table[next_key] = item = {"name": item_name, "type": item_type}
        if item_rank is not None:
            item["rank"] = item_rank
        if is_single_stigmata:
            item["is_single_stigmata"] = True
        return next_key

    def _replace_pool_item(self, loot_table, old_item_name: str, new_item_name: str) -> bool:
        old_item_id = self._find_item_id(old_item_name)
        if old_item_id is None:
            self._log(f"The item '{old_item_name}' doesn't exist, hence it won't be replaced.")
            return False
        new_item_id = self._find_item_id(new_item_name)
        if new_item_id is None:
            self._log(
                f"The item '{new_item_name}' doesn't exist, hence it won't replace the item '{old_item_name}'."
            )
            return False
        if self._replace_pool_item_internal(loot_table, old_item_id, new_item_id):
            self._log(
                f"The item '{old_item_name}' has been replaced by the item '{new_item_name}'."
            )
            return True
        self._log(
            f"The item '{old_item_name}' cannot be found in the pool, hence it won't be replaced."
        )
        return False

    def _replace_pool_valkyrie_fragment(
        self, loot_table, old_valkyrie_name: str, new_valkyrie_name: str
    ) -> bool:
        old_item_id = self._find_valkyrie_fragment_id(old_valkyrie_name)
        if old_item_id is None:
            self._log(
                f"The fragment for item '{old_valkyrie_name}' doesn't exist, hence it won't be replaced."
            )
            return False
        new_item_id = self._find_valkyrie_fragment_id(new_valkyrie_name)
        if new_item_id is None:
            self._log(
                f"The fragment for item '{new_valkyrie_name}' doesn't exist, hence it won't replace any other fragments."
            )
            return False
        if self._replace_pool_item_internal(loot_table, old_item_id, new_item_id):
            self._log(
                f"The fragment of valkyrie '{old_valkyrie_name}' has been replaced by the fragment of valkyrie '{new_valkyrie_name}'."
            )
            return True
        self._log(
            f"The fragment of valkyrie '{old_valkyrie_name}' cannot be found in the pool, hence it won't be replaced."
        )
        return False

    def _replace_pool_item_internal(self, loot_table, old_item_id: str, new_item_id: str) -> bool:
        for descriptor in loot_table:
            item_list = descriptor.get("items", [])
            if old_item_id not in item_list:
                continue
            item_list.remove(old_item_id)
            item_list.append(new_item_id)
            return True
        return False

    def _log(self, message: str):
        if not self.logs_enabled:
            return
        print(message)
