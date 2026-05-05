import re
from functools import partial

from sqlalchemy import BigInteger, Dialect, Identity, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, declared_attr, mapped_column
from sqlalchemy.orm import relationship as base_relationship

static_relationship = partial(base_relationship, lazy="raise")


class SerialPK:
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True, init=False, repr=False)


class Model(DeclarativeBase, MappedAsDataclass, AsyncAttrs, kw_only=True):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        if name.endswith("_link"):
            return name
        if name.endswith("s"):
            return f"{name}es"
        if name.endswith("y"):
            return f"{name[:-1]}ies"

        return f"{name}s"


class UnsignedInt64(TypeDecorator[int]):
    """Handles conversion between a 64-bit unsigned integer (Python)
    and a 64-bit signed integer (Database).
    """

    impl = BigInteger
    cache_ok = True

    OFFSET = 1 << 63

    def process_bind_param(self, value: int | None, dialect: Dialect) -> int | None:
        """Convert Python uint64 -> Database int64 (Write)."""
        return value - self.OFFSET if value is not None else None

    def process_result_value(self, value: int | None, dialect: Dialect) -> int | None:
        """Convert Database int64 -> Python uint64 (Read)."""
        return value + self.OFFSET if value is not None else None
