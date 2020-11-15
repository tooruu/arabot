# Table of contents
- [Table of contents](#table-of-contents)
- [Welcome to Database Editor!](#welcome-to-database-editor)
- [database.json](#databasejson)
	- [item_types](#item_types)
	- [item_ranks](#item_ranks)
	- [items](#items)
	- [pools](#pools)
- [database_editor.py](#database_editorpy)
- [gacha_simulator.py](#gacha_simulatorpy)
	- [Usage](#usage)
- [Quick tutorial on updating the gacha](#quick-tutorial-on-updating-the-gacha)

# Welcome to Database Editor!

The Database Editor is a script aiming to ease your life when it comes to creating and managing gacha loot tables ("supplies") by exposing various APIs. Let's get started, shall we?

# database.json

This file is going to be your best friend and your worst enemy. It holds all the data that you configure, *ideally* with the script. Hopefully, everything can be solved by the script, but in case something cannot be, you have to help yourself by digging into this file. Let's look at the structure of this file.

## item_types

This section is meant to define the various types of items. This is a logical grouping of items to be able to assign different behavior to items.

Properties:
* **id**: Specifies the globally unique identifier of the item type. This is the JSON object key.
* **name**: Today, it has no particular use in the application, but it helps you, *Editor-kun* identify the type.
* **is_multi**: When set to *true*, items of this type have a quantity greater than one when pulled.
* **multi_min**: Determines the minimum quantity of the items of this type when pulled. Only taken into consideration when **is_multi** is set to *true*.
* **multi_max**: Determines the maximum quantity of the items of this type when pulled. Only taken into consideration when **is_multi** is set to *true*.

Example:
```json
"item_types": {
	"0": {
		"name": "Valkyrie"
	},
	"1": {
		"name": "Equipment"
	},
	"2": {
		"name": "Soul",
		"is_multi": true,
		"multi_min": 5,
		"multi_max": 8
	}
}
```

## item_ranks

This section is meant to define the various ranks of items. For the sake of simplicity, valkyries and equipment are handled as identical types from the perspective of rank, meaning there are no ranks such as "S" or "5*". Instead we have our typical RPG naming conventions, **but** you can change it if you'd like. You could have both numbers with stars and letters/words together.

Properties:
* **id**: Specifies the globally unique identifier of the item rank. This is the JSON object key.
* **name**: Today, it has no particular use in the application, but it helps you, *Editor-kun* identify the rank.
* **is_special**: When set to *true*, the names of the items of this rank will be written in **bold**.

Example:
```json
"item_ranks": {
	"0": {
		"name": "Junk"
	},
	"1": {
		"name": "Common"
	},
	"2": {
		"name": "Uncommon"
	},
	"3": {
		"name": "Rare",
		"is_special": true
	},
	"4": {
		"name": "Epic",
		"is_special": true
	}
}
```

## items

This section is meant to define known items.

Properties:
* **id**: Specifies the globally unique identifier of the item. This is the JSON object key.
* **name**: Determines the name of the item. This is the name displayed when someone pulls the item.
* **type**: Optionally determines the type of the item. This is the identifier defined in [item_types](#item_types). It defaults to *None*.
* **rank**: Optionally determines the rank of the item. This is the identifier defined in [item_ranks](#item_ranks). It defaults to *None*.

Example:
```json
"items": {
	"589": {
		"name": "HOLA Chest",
		"type": "5"
	},
	"590": {
		"name": "Nagamitsu (M)",
		"type": "8",
		"rank": "3"
	}
}
```

## pools

This section holds the pool definitions.

Properties:
* **id**: Specifies the globally unique identifier of the pool. This is the JSON object key.
* **name**: Determines the full name of the supply.
* **available**: When set to *true*, the supply can be pulled by people.
* **loot_table**: An *array* that holds the loot table descriptors:
  * **rate**: A single-precision floating-point number between that specifies the rate at which each item can be pulled (see *items* below).
  * **items**: An *array* that holds the identifiers of the items that can be pulled at the specified rate.

Example:
```json
"pools": {
	"ex": {
		"name": "Expansion Battlesuit",
		"available": true,
		"loot_table": [
			{
				"rate": 0.015,
				"items": [
					"539"
				]
			},
			{
				"rate": 0.03,
				"items": [
					"559",
					"572",
					"542",
				]
			}
		]
	}
}
```

# database_editor.py

This is the script that provides methods for editing the [database.json](#databasejson) file without having to use a text editor.

Arguments:
* **--type**: Specifies the identifier of the item type.
* **--rank**: Specifies the identifier of the item rank.
* **--single**: When this flag is set, the item is considered to be a single-piece stigmata.
* **--awakened**: When this flag is set, the item is considered to be an awakened Valkyrie battlesuit.
* **--field**: Specifies the name of the field used by the command.
* **--pool**: Specifies the identifier of the pool.
* **--rate**: Specifies the desired drop rate.
* **--fragments**: Specifies that the valkyrie fragments/souls should automatically be handled.
* **operation**: Specifies the command to be executed. Always mandatory.
  * Generic commands
    * **listtables**: Lists the tables available in [database.json](#databasejson).
  * Item related commands
    * **additem**: Adds a new item to the database. Arguments: **--type**, --rank, --single
    * **finditem**: Finds an item in the database. Arguments: **--field**
    * **deleteitem**: Deletes an item from the database. Arguments: --field
    * **additemset**: Adds an entire set of items, including a valkyrie battlesuit, a weapon and a stigmata set. Arguments: --awakened, --rank
  * Pool related commands
    * **addpool**: Adds a new pool to the database.
    * **removepool**: Removes an existing pool from the database.
    * **addpoolitem**: Adds an item to a pool. Arguments: **--pool**, **--rate**
    * **removepoolitem**: Removes an item from a pool. Arguments: **--pool**
    * **replacepoolitem**: Replaces an item in a pool with another one. Arguments: **--pool**, --fragments
    * **showpool**: Shows the items in a pool.
    * **togglepool**: Toggles the availability of a pool.
    * **clonepool**: Clones a pool with a new identifier and name.
* **names**: Always mandatory.

Example for adding items:

> database_editor.py --type 1 --rank 0 additem "Proto Pulse Tachi" "Seishuu Muramasa"

This command is typically useful when a new item is introduced to the game or the database is missing an existing one.

Example for creating a pool and adding items to it:

> database_editor.py addpool focb "Focused Supply B"  
> database_editor.py --rate 0.0248 --pool focb addpoolitem "Nue of the Shadow"

This is useful when a new supply needs to be created from scratch or items have to be added to an existing pool. Don't forget to adjust the rates in case it's needed!

Example for cloning a pool:

> database_editor.py clonepool focb foca "Focused Supply A"

This is typically useful when a new supply has almost identical items and rates.

Example for replacing an item in a pool:

> database_editor.py --pool foca replaceitem "Nue of the Shadow" "Swan Lake"

This is typically useful when a supply changes only a few of the items but not the rates.

# gacha_simulator.py

This is our most favourite script - it is used to simulate the Honkai Impact 3rd gacha by using the data defined in [database.json](#databasejson).

## Usage

Just invoke the script with the ID of the pool you'd like to pull as follows:

> gacha_simulator.py ex

You should see an output similar to the following:

> Available pools:  
> ex focb foca dorm dormeq  
> ***Expansion Battlesuit** supply drops:*  
> Swallowtail Phantasm fragment x4  
> Phase Shifter  
> **Herrscher of Thunder**  
> Phase Shifter  
> Phantom Iron  
> ADV EXP Chip  
> Swallowtail Phantasm fragment x5  
> Luna Kindred  
> HOLI Chest  
> Luna Kindred soul x6

# Quick tutorial on updating the gacha

Updating the Expansion Battlesuit Supply is typically as simple as replacing a few battlesuits and fragments.

First, figure out what are the items you have to replace:

> database_editor.py showpool ex

Then, simply replace them with the appropriate items:

> database_editor.py --pool ex --fragments replacepoolitem "Herrscher of Thunder" "Azure Empyrea" "Swallowtail Phantasm" "Wolf's Dawn" "Luna Kindred" "Blueberry Blitz" "Phantom Iron" "Arctic Kriegsmesser" "Yamabuki Armor" "Shadow Dash"

Since you most likely want to replace the valkyrie fragments/souls, too, specify the *--fragments* flag to have the script automatically do it. Otherwise, you have to manually replace them.

The above should give you an output similar to this (unless one or more of the items cannot be found):

> The item 'Herrscher of Thunder' has been replaced by the item 'Azure Empyrea'.  
> The fragment of valkyrie 'Herrscher of Thunder' has been replaced by the fragment of valkyrie 'Azure Empyrea'.  
> The item 'Swallowtail Phantasm' has been replaced by the item 'Wolf's Dawn'.  
> The fragment of valkyrie 'Swallowtail Phantasm' has been replaced by the fragment of valkyrie 'Wolf's Dawn'.  
> The item 'Luna Kindred' has been replaced by the item 'Blueberry Blitz'.  
> The fragment of valkyrie 'Luna Kindred' has been replaced by the fragment of valkyrie 'Blueberry Blitz'.  
> The item 'Phantom Iron' has been replaced by the item 'Arctic Kriegsmesser'.  
> The fragment of valkyrie 'Phantom Iron' has been replaced by the fragment of valkyrie 'Arctic Kriegsmesser'.  
> The item 'Yamabuki Armor' has been replaced by the item 'Shadow Dash'.  
> The fragment of valkyrie 'Yamabuki Armor' has been replaced by the fragment of valkyrie 'Shadow Dash'.  
> The database has been saved successfully.

To update a Focused Supply, you issue the same command but typically, you don't need the *--fragments* flag, because these supplies have no valkyries:

> database_editor.py --pool foca replacepoolitem "Swan Lake" "Nebulous Duality" "Hyper Railguns" "ARC Serratus" "Void Blade" "Ice Epiphyllum" "Briareus PRI" "Raikiri" "Sleeping Beauty" "Star Shatterer: Vikrant" "Cinder Hawk" "11th Sacred Relic" "Genome Reaper" "Aphrodite" "Beethoven" "Fu Hua: Margrave" "Caravaggio" "Welt Yang" "Michelangelo" "Wilde" "Nobel" "Gustav Klimt" "Isaac Newton" "Kallen - Hymn"

Similar to the above, you get an output similar to the following:

> The item 'Swan Lake' has been replaced by the item 'Nebulous Duality'.  
> The item 'Hyper Railguns' has been replaced by the item 'ARC Serratus'.  
> The item 'Void Blade' has been replaced by the item 'Ice Epiphyllum'.  
> The item 'Briareus PRI' has been replaced by the item 'Raikiri'.  
> The item 'Sleeping Beauty' has been replaced by the item 'Star Shatterer: Vikrant'.  
> The item 'Cinder Hawk' has been replaced by the item '11th Sacred Relic'.  
> The item 'Genome Reaper' has been replaced by the item 'Aphrodite'.  
> The item 'Beethoven' has been replaced by the item 'Fu Hua: Margrave'.  
> The item 'Caravaggio' has been replaced by the item 'Welt Yang'.  
> The item 'Michelangelo' has been replaced by the item 'Wilde'.  
> The item 'Nobel' has been replaced by the item 'Gustav Klimt'.  
> The item 'Isaac Newton' has been replaced by the item 'Kallen - Hymn'.  
> The database has been saved successfully.

Once you've finished updating the pools, you can give gacha a few tries as described in the section [gacha_simulator.py](#gacha_simulatorpy).