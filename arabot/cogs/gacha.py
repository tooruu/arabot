import logging
from collections.abc import Generator

from arabot.core import Category, Ara, Cog, Context
from arabot.utils import bold, underline
from disnake import DiscordException
from disnake.ext.commands import (
    BadArgument,
    BucketType,
    CommandOnCooldown,
    MissingRequiredArgument,
    command,
    cooldown,
)

from gacha.logging import LogBase, LogLevel
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

DATABASE_FILE_PATH = "resources/database.json"
LOG_LEVEL = LogLevel.WARNING

STIGMATA_PARTS = "T", "M", "B"
STIGMATA_PARTS_FULL = tuple(f"({part})" for part in STIGMATA_PARTS)


class ItemResolver(ItemResolverInterface):
    def __init__(self, entity_provider: EntityProviderInterface, log: LogBase):
        super().__init__(entity_provider)
        self._log = log

    def resolve(self, item_id: int) -> Generator[VirtualItem, None, None]:
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


class Gacha(Cog, category=Category.GAMES):
    def __init__(self, ara: Ara):
        self.ara = ara
        self._pull_provider = Gacha._initialize_pull_provider()

    @cooldown(1, 60, BucketType.user)
    @command(
        aliases=["pull"],
        brief="Try out your luck for free",
        cooldown_after_parsing=True,
    )
    async def gacha(self, ctx: Context, supply_type: str, pull_count: int = 10):
        supply_type = supply_type.casefold()
        if not self._pull_provider.has_pool(supply_type):
            await ctx.reply("The supply type you specified doesn't exist")
            self.gacha.reset_cooldown(ctx)
            return
        pulls = self._pull_provider.pull(supply_type, pull_count)
        formatted_pulls = self._format_pulls(pulls)

        supply_name = bold(self._pull_provider.get_pool_name(supply_type))
        header = underline(supply_name + " supply drops:\n")
        await ctx.reply(header + "\n".join(formatted_pulls))

    @gacha.error
    async def on_error(self, ctx: Context, error: DiscordException):
        if isinstance(error, CommandOnCooldown):
            return
        if isinstance(error, MissingRequiredArgument):
            pools = [
                f"{bold(pool_code)} - {self._pull_provider.get_pool_name(pool_code)}"
                for pool_code in self._pull_provider.get_pool_codes()
            ]
            await ctx.send("Currently available supplies:\n" + "\n".join(pools))
            return
        last_param = ctx.command.clean_params.popitem()[1]
        if (
            isinstance(error, BadArgument)
            and last_param.name in str(error)
            and last_param.annotation.__name__ in str(error)
        ):
            await ctx.reply(
                f"Cooldown expires in {self.gacha.get_cooldown_retry_after(ctx):.0f} seconds"
                if self.gacha.is_on_cooldown(ctx)
                else "You specified an invalid amount"
            )
            return
        await ctx.reply("An error occurred")
        self.gacha.reset_cooldown(ctx)
        raise error

    @staticmethod
    def _initialize_pull_provider() -> SimplePullProvider:
        log = logging
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
    def _format_pulls(pulls: Generator[Pull, None, None]) -> Generator[str, None, None]:
        for pull in pulls:
            formatted_pull = pull.name
            if pull.count > 1:
                formatted_pull = f"{formatted_pull} x{pull.count}"
            if pull.is_rare:
                formatted_pull = bold(formatted_pull)
            yield formatted_pull


def setup(ara: Ara):
    ara.add_cog(Gacha(ara))
