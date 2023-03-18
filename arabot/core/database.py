from async_lru import alru_cache
from prisma import Prisma


def ulong_to_long(uint64: int) -> int:
    # Snowflake is a ulong which is not supported by MongoDB so we convert it to signed long
    return uint64 - 2**64 // 2


class AraDB(Prisma):
    @alru_cache
    async def get_guild_prefix(self, guild_id: int) -> str | None:
        guild = {"guild_id": ulong_to_long(guild_id)}
        return row.prefix if (row := await self.prefix.find_unique(guild)) else None

    async def set_guild_prefix(self, guild_id: int, prefix: str) -> None:
        guild = {"guild_id": ulong_to_long(guild_id)}
        await self.prefix.upsert(
            guild,
            {
                "create": {"prefix": prefix} | guild,
                "update": {"prefix": prefix},
            },
        )
        self.get_guild_prefix.cache_invalidate(guild_id)

    @alru_cache
    async def get_guild_rr_kick(self, guild_id: int) -> bool | None:
        guild = {"guild_id": ulong_to_long(guild_id)}
        return row.kick_enabled if (row := await self.rrkick.find_unique(guild)) else None

    async def set_guild_rr_kick(self, guild_id: int, enable: bool) -> None:
        guild = {"guild_id": ulong_to_long(guild_id)}
        await self.rrkick.upsert(
            guild,
            {
                "create": {"kick_enabled": enable} | guild,
                "update": {"kick_enabled": enable},
            },
        )
        self.get_guild_rr_kick.cache_invalidate(guild_id)
