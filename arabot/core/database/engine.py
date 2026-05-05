import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from arabot.core.config import Config
from arabot.core.database.base import Model

logger = logging.getLogger(__name__)


@asynccontextmanager
async def init_db(drop: bool = False) -> AsyncGenerator[AsyncEngine]:
    global LocalSessionFactory

    url = make_url(Config.database_url)
    backend = url.get_backend_name()

    connect_args = {}
    match backend:
        case "sqlite":
            connect_args["check_same_thread"] = False
            connect_args["timeout"] = 10
        case "postgresql" if url.get_driver_name() in ["psycopg", "psycopg_async"]:
            connect_args["connect_timeout"] = 10
            connect_args["options"] = "-c timezone=UTC"
        case "postgresql" if url.get_driver_name() == "psycopg2":
            connect_args["timeout"] = 10
        case _:
            pass

    engine = create_async_engine(url, connect_args=connect_args)
    LocalSessionFactory = sessionmaker(engine, class_=AsyncSession, autoflush=False, expire_on_commit=False)

    if backend == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(conn: DBAPIConnection, _connection_record) -> None:
            logger.info("New database connection opened. Setting SQLite pragmas...")
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    async with engine.begin() as conn:
        if drop:
            await conn.run_sync(Model.metadata.drop_all)
        await conn.run_sync(Model.metadata.create_all)

    try:
        yield engine
    finally:
        logger.info("Disposing database engine...")
        await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    async with LocalSessionFactory.begin() as session:
        yield session
