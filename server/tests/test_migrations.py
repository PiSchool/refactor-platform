from __future__ import annotations

import os

import pytest
from sqlalchemy import inspect, select, text


def _alembic_head() -> str:
    """The revision the shipped scripts end at.

    Read rather than written down: a test that names the head has to be edited
    with every migration, and the assertion it is making is "the database is at
    head", not "the head is called this".
    """
    from pathlib import Path

    from alembic.config import Config
    from alembic.script import ScriptDirectory

    server_dir = Path(__file__).resolve().parents[1]
    return ScriptDirectory.from_config(Config(str(server_dir / "alembic.ini"))).get_current_head()


PLATFORM_TABLES = {
    "agent_session",
    "agent_tool",
    "benchmark",
    "run",
    "run_task",
    "runtime_setting",
    "task",
    "task_result",
}


async def _table_names(engine) -> set[str]:
    async with engine.connect() as connection:
        return await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )


@pytest.mark.asyncio
async def test_fresh_database_is_upgraded_to_alembic_head(tmp_env, monkeypatch):
    from app.db import engine as db_engine
    from app.db.models import Base

    def reject_create_all(*_args, **_kwargs):
        raise AssertionError("migrate must run Alembic revisions, not metadata.create_all")

    monkeypatch.setattr(Base.metadata, "create_all", reject_create_all)

    await db_engine.migrate()

    engine = db_engine.get_engine()
    assert PLATFORM_TABLES <= await _table_names(engine)
    async with engine.connect() as connection:
        revision = (
            await connection.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one()
    assert revision == _alembic_head()

    await db_engine.migrate()
    assert PLATFORM_TABLES <= await _table_names(engine)


@pytest.mark.asyncio
async def test_existing_stamped_database_is_adopted_without_data_loss(tmp_env):
    from app.db import engine as db_engine
    from app.db.models import Base, Benchmark

    engine = db_engine.get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(
                "CREATE TABLE alembic_version "
                "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
            )
        )
        await connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('v1_initial')")
        )

    async with db_engine.session_factory()() as session:
        session.add(
            Benchmark(
                key="preserved",
                name="Preserved benchmark",
                language="python",
                manifest={"source": "before-alembic"},
            )
        )
        await session.commit()

    await db_engine.migrate()

    async with db_engine.session_factory()() as session:
        benchmark = (
            await session.execute(select(Benchmark).where(Benchmark.key == "preserved"))
        ).scalar_one()
    assert benchmark.manifest == {"source": "before-alembic"}
    assert PLATFORM_TABLES <= await _table_names(engine)
    async with engine.connect() as connection:
        revision = (
            await connection.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one()
    assert revision == _alembic_head()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_migrates_to_head_with_jsonb(monkeypatch):
    database_url = os.getenv("PLATFORM_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("PLATFORM_TEST_DATABASE_URL is not configured")

    from app import config
    from app.db import engine as db_engine
    from app.db.models import Base

    await db_engine.dispose()
    monkeypatch.setenv("DATABASE_URL", database_url)
    config.get_settings.cache_clear()
    engine = db_engine.get_engine()
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.execute(text("DROP TABLE IF EXISTS alembic_version"))

        await db_engine.migrate()

        async with engine.connect() as connection:
            revision = (
                await connection.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one()
            config_type = (
                await connection.execute(
                    text(
                        "SELECT data_type FROM information_schema.columns "
                        "WHERE table_schema = current_schema() "
                        "AND table_name = 'run' AND column_name = 'config'"
                    )
                )
            ).scalar_one()
        assert revision == _alembic_head()
        assert config_type == "jsonb"
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
        await db_engine.dispose()
        config.get_settings.cache_clear()