from async_lru import alru_cache
from prisma import Prisma


class AraDB(Prisma):
    @alru_cache(cache_exceptions=False)
    async def get_guild_prefix(self, guild_id: int) -> str | None:
        return getattr(await self.prefix.find_unique({"guild_id": str(guild_id)}), "prefix", None)

    async def set_guild_prefix(self, guild_id: int, prefix: str) -> None:
        identifier = {"guild_id": str(guild_id)}
        await self.prefix.upsert(
            identifier,
            {
                "create": {"prefix": prefix} | identifier,
                "update": {"prefix": prefix},
            },
        )
