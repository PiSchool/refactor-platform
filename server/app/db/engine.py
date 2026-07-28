"""Async database engine, sessions, and Alembic migration entry point."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine
    if _engine is None:
        url = get_settings().resolved_database_url()
        kwargs: dict = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"timeout": 30}
        _engine = create_async_engine(url, **kwargs)
        if url.startswith("sqlite"):
            @event.listens_for(_engine.sync_engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, _record):
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA foreign_keys=ON")
                cur.execute("PRAGMA busy_timeout=30000")
                cur.close()
    return _engine


def session_factory() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def migrate() -> None:
    """Apply every committed Alembic revision to the configured database."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(upgrade_connection_to_head)


def upgrade_connection_to_head(connection) -> None:
    """Upgrade an already-open SQLAlchemy connection to the schema head."""
    server_dir = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(server_dir / "alembic.ini"))
    alembic_config.attributes["connection"] = connection
    command.upgrade(alembic_config, "head")


async def dispose() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


def reset_for_tests() -> None:
    global _engine, _sessionmaker
    _engine = None
    _sessionmaker = None
