import logging
from argparse import ArgumentParser
from collections.abc import Callable, Generator, Iterable
from typing import TypeVar

from gacha.logging import ConsoleLog, LogBase, LogLevel
from gacha.models import VirtualItem
from gacha.models.pulls import Pull
from gacha.persistence.json import JsonEntityProvider
from gacha.persistence.json.converters import (
    ItemConverter,
    ItemRankConverter,
    ItemTypeConverter,
    PoolConverter,
)
from gacha.providers import EntityProviderInterface, SimplePullProvider
from gacha.resolvers import ItemResolverInterface
from gacha.utils.entity_provider_utils import get_item, get_item_rank, get_item_type

# ::: Usage examples :::
# Pull 10 items from the "foca" supply:
# python tools/gacha_simulator.py foca
# Pull 100 items from the "foca" supply, consolidate and sort them:
# python tools/gacha_simulator.py -c -s foca 100

DATABASE_FILE_PATH = "resources/database.json"
LOG_LEVEL = LogLevel.INFORMATION
STIGMATA_PARTS = ("T", "M", "B")
STIGMATA_PARTS_FULL = tuple(f"({part})" for part in STIGMATA_PARTS)

_T = TypeVar("_T")
_T2 = TypeVar("_T2")


class ItemResolver(ItemResolverInterface):
    def __init__(self, entity_provider: EntityProviderInterface, log: LogBase):
        super().__init__(entity_provider)
        self._log = log

    def resolve(self, item_id: int) -> Generator[VirtualItem]:
        item = get_item(self._entity_provider, item_id)
        if not item:
            self._log.warning(f"The configured item identified by '{item_id}' doesn't exist.")
            return
        item_type = get_item_type(self._entity_provider, item.item_type_id)
        if not item_type:
            self._log.warning(
                f"The configured item type identified by '{item.item_type_id}' doesn't exist."
            )
            return
        item_rank = get_item_rank(self._entity_provider, item.rank_id)
        if not item_rank:
            self._log.warning(
                f"The configured item rank identified by '{item.rank_id}' doesn't exist."
            )
            return
        if item_type.name == "Stigmata" and not item.name.endswith(STIGMATA_PARTS_FULL):
            item_names = [f"{item.name} ({part})" for part in STIGMATA_PARTS]
        else:
            item_names = [item.name]
        for item_name in item_names:
            yield VirtualItem(item.id, item_name)


class GachaSimulator:
    def __init__(self) -> None:
        self._pull_provider = GachaSimulator._initialize_pull_provider()

    @staticmethod
    def _initialize_pull_provider() -> SimplePullProvider:
        log = ConsoleLog(LOG_LEVEL)
        entity_provider = JsonEntityProvider(
            DATABASE_FILE_PATH,
            log,
            [
                ItemConverter(),
                ItemRankConverter(),
                ItemTypeConverter(),
                PoolConverter(),
            ],
        )
        item_resolver = ItemResolver(entity_provider, log)
        return SimplePullProvider(entity_provider, item_resolver, log)

    @staticmethod
    def _aggregate(source: Iterable[_T], seed: _T2, func: Callable[[_T2, _T], _T2]) -> _T2:
        current_value = seed
        for item in source:
            current_value = func(current_value, item)
        return current_value

    def get_pool_codes(self):
        return self._pull_provider.get_pool_codes()

    def pull(
        self,
        supply_type: str,
        pull_count: int = 10,
        consolidate: bool = False,
        sort: bool = False,
    ):
        # Change the allowed pull count to support any value.
        self._pull_provider.pull_count_min = 1
        self._pull_provider.pull_count_max = pull_count

        supply_type = supply_type.casefold()
        if not self._pull_provider.has_pool(supply_type):
            logging.error("Attempted to pull from an invalid supply.")
            return
        pulls = self._pull_provider.pull(supply_type, pull_count)
        if consolidate:
            pulls = GachaSimulator._aggregate(
                pulls, {}, lambda c, p: GachaSimulator._consolidate(c, p)
            ).values()
        if sort:
            pulls = sorted(pulls, key=lambda pull: pull.name)
        formatted_pulls = [
            f'{pull.name} x{pull.count}{" (Rare)" if pull.is_rare else ""}' for pull in pulls
        ]

        logging.info(
            "The supply '%s' provided the following items %s",
            self._pull_provider.get_pool_name(supply_type),
            "\n".join(formatted_pulls),
        )

    @staticmethod
    def _consolidate(dictionary: dict[str, Pull], pull: Pull) -> dict[str, Pull]:
        key = f"{pull.id}/{pull.name}"
        try:
            dictionary[key].value += pull.count
        except KeyError:
            dictionary[key] = Pull(pull.id, pull.name, pull.count, pull.is_rare)
        return dictionary


parser = ArgumentParser()
parser.add_argument("-c", "--consolidate", dest="consolidate", action="store_const", const=True)
parser.add_argument("-s", "--sort", dest="sort", action="store_const", const=True)
parser.add_argument("pool")
parser.add_argument("count", nargs="?", default=10)
args = parser.parse_args()

gacha = GachaSimulator()
logging.info("Available pools: %s", ", ".join(gacha.get_pool_codes()))
gacha.pull(args.pool, int(args.count), bool(args.consolidate), bool(args.sort))
