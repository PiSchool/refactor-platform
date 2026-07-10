from __future__ import annotations

import pytest
from sqlalchemy import select


@pytest.mark.asyncio
async def test_round_trip_run_chain(tmp_env):
    from app.db import engine as db_engine
    from app.db.models import AgentSession, AgentTool, Benchmark, Run, RunTask, Task, TaskResult

    await db_engine.migrate()
    async with db_engine.session_factory()() as s:
        bench = Benchmark(key="fixturebench", name="Fixture", language="python", manifest={})
        tool = AgentTool(key="stub", name="Stub", manifest={})
        s.add_all([bench, tool])
        await s.flush()
        task = Task(
            benchmark_id=bench.id, task_key="t1", title="T1", language="python",
            workspace={"type": "snapshot", "source": "repo"}, instructions="do it", params={"mode": "base"},
        )
        s.add(task)
        await s.flush()
        run = Run(benchmark_id=bench.id, agent_tool_id=tool.id, setup_key="s1",
                  model="openrouter/free", task_timeout_seconds=600)
        s.add(run)
        await s.flush()
        rt = RunTask(run_id=run.id, task_id=task.id, ordinal=0, timeout_seconds=600)
        s.add(rt)
        await s.flush()
        s.add(TaskResult(run_task_id=rt.id, passed=True, tokens_input=10, tokens_output=5,
                         metrics={"passRate": 1.0}, details={"applySucceeded": True}))
        s.add(AgentSession(run_task_id=rt.id, pid=123, terminal_path="x/terminal.log"))
        await s.commit()

    async with db_engine.session_factory()() as s:
        row = (await s.execute(select(TaskResult))).scalar_one()
        assert row.passed is True
        assert row.details["applySucceeded"] is True
        rt = (await s.execute(select(RunTask))).scalar_one()
        assert rt.status == "pending"


@pytest.mark.asyncio
async def test_task_unique_per_benchmark(tmp_env):
    from app.db import engine as db_engine
    from app.db.models import Benchmark, Task

    await db_engine.migrate()
    async with db_engine.session_factory()() as s:
        bench = Benchmark(key="b", name="B", language="python", manifest={})
        s.add(bench)
        await s.flush()
        s.add(Task(benchmark_id=bench.id, task_key="k", title="a", language="python",
                   workspace={}, params={}))
        await s.commit()
    async with db_engine.session_factory()() as s:
        s.add(Task(benchmark_id=bench.id, task_key="k", title="b", language="python",
                   workspace={}, params={}))
        with pytest.raises(Exception):
            await s.commit()
