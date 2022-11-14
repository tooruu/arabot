from async_lru import alru_cache
from prisma import Prisma


class AraDB(Prisma):
    @alru_cache(cache_exceptions=False)
    async def get_guild_prefix(self, guild_id: int) -> str | None:
        # Snowflake is a ulong which is not supported by MongoDB so we convert it to signed long
        guild = {"guild_id": guild_id - 2**64 // 2}
        return row.prefix if (row := await self.prefix.find_unique(guild)) else None

    async def set_guild_prefix(self, guild_id: int, prefix: str) -> None:
        guild = {"guild_id": guild_id - 2**64 // 2}
        await self.prefix.upsert(
            guild,
            {
                "create": {"prefix": prefix} | guild,
                "update": {"prefix": prefix},
            },
        )
