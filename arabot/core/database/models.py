from asyncio import Future
from functools import _make_key

from async_lru import _CacheItem, alru_cache
from sqlalchemy import UniqueConstraint, select
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import Mapped, mapped_column

from arabot.core.database.base import Model, SerialPK, UnsignedInt64
from arabot.core.database.engine import get_session
from arabot.core.enums import SettingKey

type Json = dict | list | str | int | bool | None


class Setting(Model, SerialPK):
    __table_args__ = (UniqueConstraint("key", "guild_id"),)

    key: Mapped[SettingKey] = mapped_column(nullable=False)
    value: Mapped[Json] = mapped_column(JSONB, nullable=False)
    guild_id: Mapped[int | None] = mapped_column(UnsignedInt64, default=None)

    @classmethod
    @alru_cache(maxsize=None)
    async def get(cls, key: SettingKey, guild_id: int | None = None) -> Json:
        async with get_session() as session:
            stmt = select(cls.value).where(cls.key == key)
            if guild_id is not None:
                stmt = stmt.where(cls.guild_id == guild_id)

            return await session.scalar(stmt)

    @classmethod
    async def set(cls, key: SettingKey, value: Json, guild_id: int | None = None) -> Json:
        async with get_session() as session:
            stmt = insert(cls).values(key=key, value=value, guild_id=guild_id)
            stmt = stmt.on_conflict_do_update(index_elements=["key", "guild_id"], set_={"value": stmt.excluded.value})
            stmt = stmt.returning(cls.value)
            actual_value = await session.scalar(stmt)

        cls.cache_result(key, guild_id, actual_value)
        return actual_value

    @classmethod
    def cache_result(cls, key: SettingKey, guild_id: int | None, value: Json) -> None:
        if guild_id is None:
            # Assume the caller doesn't explicitly pass the default value of None
            cache_key = (cls, key)
            # Invalidate the explicit None in case the caller wants to pass it
            cls.get.cache_invalidate(cls, key, guild_id)
            # Not caching this variant to save memory since the short variant of the function call is preferred
        else:
            cache_key = (cls, key, guild_id)

        fut = Future()
        fut.set_result(value)
        cache_key = _make_key(cache_key, {}, cls.get._LRUCacheWrapper__typed)
        cls.get._LRUCacheWrapper__cache[cache_key] = _CacheItem(fut, None, 0)
