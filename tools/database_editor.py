# Neat hack to make sure this script can import modules despite being invoked from within the same package.
# See: https://stackoverflow.com/a/16985066
import sys
import os

PACKAGE_PARENT = ".."
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from tools.modules.database_editor import DatabaseEditor
from argparse import ArgumentParser
from json import dump, load

DATABASE_FILE_PATH = "./bot/res/database.json"


# TODO LIST
# - changerate command
#   change the rate of a specific item set
#   e.g. --pool ex changerate 0.15 0.07
#   note: it should merge equal sets
# - interactive pool updates
#   it would be nice if the user didn't have to type the whole name of items
#   but could instead use regex matching (eg. "Star Shatterer: Vikrant" -> "vikrant")
#   and in case the input is ambiguous the script should let the user choose one
#   from the list of matching options
# - smarter argparse
#   it sucks when you have to type unnecessary parameters
#   such as the listtables command
class Main:
    def __init__(self, database_file_path: str):
        self._database_file_path = database_file_path
        with open(database_file_path) as database_file:
            self._editor = DatabaseEditor(load(database_file))
        self._operations = {
            # generic
            "listtables": self._editor.list_tables,
            # items
            "additem": self._editor.add_item,
            "finditem": self._editor.find_item,
            "deleteitem": self._editor.delete_item,
            "additemset": self._editor.add_item_set,
            # pools
            "addpool": self._editor.add_pool,
            "removepool": self._editor.remove_pool,
            "addpoolitem": self._editor.add_pool_item,
            "removepoolitem": self._editor.remove_pool_item,
            "replacepoolitem": self._editor.replace_pool_item,
            "showpool": self._editor.show_pool,
            "togglepool": self._editor.toggle_pool,
            "clonepool": self._editor.clone_pool,
        }

    def execute(self, options):
        operation = self._operations.get(options.operation)
        if operation is not None:
            print(f"Invoking operation '{options.operation}'...")
            has_database_changed = operation(options)
            if has_database_changed:
                self._save_database()
            print(f"Operation '{options.operation}' finished.")
        else:
            print(f"Invalid operation '{options.operation}'.")

    def _save_database(self):
        """Saves the database associated to the editor instance."""
        with open(self._database_file_path, "w+") as database_file:
            dump(self._editor.database, database_file, indent="\t")
        print("The database has been saved successfully.")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--type", default="0")  # Item type
    parser.add_argument("--rank", default=None)  # Item rank
    parser.add_argument("--single", action="store_const", const=True)  # Is single (non-set) stigmata?
    parser.add_argument("--awakened", action="store_const", const=True)  # Is awakened valkyrie?
    parser.add_argument("--field", default=None)  # Field name
    parser.add_argument("--pool", default=None)  # Pool ID
    parser.add_argument("--rate", default=None)  # Drop rate
    parser.add_argument(
        "--fragments", action="store_const", const=True
    )  # Automatically handles valkyrie fragments/souls during item operations
    parser.add_argument(
        "--regex", action="store_const", const=True
    )  # Handles the values of "names" as regular expressions
    parser.add_argument("operation")  # Operation to perform
    parser.add_argument("names", nargs="+")
    Main(DATABASE_FILE_PATH).execute(parser.parse_args())
