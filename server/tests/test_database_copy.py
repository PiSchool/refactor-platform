from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import select, text


def _sqlite_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path}"


@pytest.fixture()
async def populated_source(tmp_env):
    from app.db import engine as db_engine
    from app.db.models import AgentTool, Benchmark, Run, RunTask, RuntimeSetting, Task, TaskResult

    await db_engine.migrate()
    async with db_engine.session_factory()() as session:
        benchmark = Benchmark(
            key="copy-benchmark",
            name="Copy benchmark",
            language="python",
            manifest={"nested": {"enabled": True}},
        )
        agent = AgentTool(
            key="copy-agent",
            name="Copy agent",
            manifest={"models": ["fixture"]},
        )
        session.add_all([benchmark, agent])
        await session.flush()
        task = Task(
            benchmark_id=benchmark.id,
            task_key="copy-task",
            title="Copy task",
            language="python",
            workspace={"type": "snapshot", "source": "fixture"},
            instructions="copy it",
            params={"ordinal": 1},
        )
        session.add(task)
        await session.flush()
        run = Run(
            benchmark_id=benchmark.id,
            agent_tool_id=agent.id,
            setup_key="s1",
            model="fixture",
            status="completed",
            config={"copied": True},
            task_timeout_seconds=60,
        )
        session.add(run)
        await session.flush()
        run_task = RunTask(
            run_id=run.id,
            task_id=task.id,
            ordinal=0,
            status="passed",
            timeout_seconds=60,
        )
        session.add(run_task)
        await session.flush()
        session.add(
            TaskResult(
                run_task_id=run_task.id,
                passed=True,
                reason="passed",
                metrics={"score": 1.0},
                details={"nested": [1, 2, 3]},
            )
        )
        session.add(RuntimeSetting(key="copy-setting", value={"value": 7}))
        await session.commit()

    source = tmp_env / "data" / "platform.db"
    await db_engine.dispose()
    return source, run.id


@pytest.mark.asyncio
async def test_copy_preserves_all_rows_and_is_idempotent(populated_source, tmp_path):
    from app.db.copy_database import copy_platform_database, inspect_platform_database

    source, run_id = populated_source
    destination = tmp_path / "destination.db"

    first = await copy_platform_database(source, _sqlite_url(destination))
    second = await copy_platform_database(source, _sqlite_url(destination))

    assert first.status == "copied"
    assert second.status == "already_present"
    assert first.tables == second.tables
    assert first.tables["run"].count == 1
    assert first.tables["task_result"].count == 1

    snapshot = await inspect_platform_database(_sqlite_url(destination))
    assert snapshot == first.tables

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.db.models import Run

    engine = create_async_engine(_sqlite_url(destination))
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        copied_run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one()
    assert copied_run.config == {"copied": True}
    await engine.dispose()


@pytest.mark.asyncio
async def test_copy_refuses_a_conflicting_nonempty_destination(populated_source, tmp_path):
    from app.db.copy_database import (
        DestinationConflict,
        copy_platform_database,
        inspect_platform_database,
    )
    from app.db.models import RuntimeSetting
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    source, _run_id = populated_source
    destination = tmp_path / "destination.db"
    destination_url = _sqlite_url(destination)
    await copy_platform_database(source, destination_url)

    engine = create_async_engine(destination_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        setting = await session.get(RuntimeSetting, "copy-setting")
        setting.value = {"value": "conflict"}
        await session.commit()
    await engine.dispose()

    with pytest.raises(DestinationConflict, match="does not exactly match"):
        await copy_platform_database(source, destination_url)

    source_snapshot = await inspect_platform_database(_sqlite_url(source))
    assert source_snapshot["runtime_setting"].count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_copy_to_postgres_is_verified_and_idempotent(populated_source):
    database_url = os.getenv("PLATFORM_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("PLATFORM_TEST_DATABASE_URL is not configured")

    from app.db.copy_database import copy_platform_database
    from app.db.models import Base
    from sqlalchemy.ext.asyncio import create_async_engine

    source, _run_id = populated_source
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.execute(text("DROP TABLE IF EXISTS alembic_version"))

        first = await copy_platform_database(source, database_url)
        second = await copy_platform_database(source, database_url)
        assert first.status == "copied"
        assert second.status == "already_present"
        assert first.tables == second.tables

        async with engine.connect() as connection:
            json_type = (
                await connection.execute(
                    text(
                        "SELECT data_type FROM information_schema.columns "
                        "WHERE table_schema = current_schema() "
                        "AND table_name = 'task_result' AND column_name = 'details'"
                    )
                )
            ).scalar_one()
        assert json_type == "jsonb"
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
        await engine.dispose()