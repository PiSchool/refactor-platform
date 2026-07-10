"""In-process run worker: durable queued rows + asyncio signal (instant start),
boot drain, strictly sequential. Owns lifecycle actions (stop/skip/restart/
delete) against the active run.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.catalog.loader import Registry
from app.db import engine as db_engine
from app.db.models import Run, RunTask, TaskResult, new_id, utcnow
from app.execution.pty_host import kill_pid_group
from app.execution.taskloop import RunControl, execute_run
from app.realtime.hub import Hub


class Worker:
    def __init__(self, registry: Registry, hub: Hub) -> None:
        self.registry = registry
        self.hub = hub
        self._signal = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._controls: dict[str, RunControl] = {}
        self._running = False

    async def start(self) -> None:
        self.hub.bind_loop(asyncio.get_running_loop())
        await self._reconcile_orphans()
        self._running = True
        self._signal.set()  # drain any leftover queued rows on boot
        self._task = asyncio.create_task(self._loop())

    async def _reconcile_orphans(self) -> None:
        """A restart or crash leaves rows marked `running` with no process
        behind them. Without this they stay 'running' in the UI forever."""
        async with db_engine.session_factory()() as s:
            runs = (await s.execute(select(Run).where(Run.status == "running"))).scalars().all()
            if not runs:
                return
            ids = [r.id for r in runs]
            for run in runs:
                run.status = "error"
                run.finished_at = utcnow()
            tasks = (await s.execute(select(RunTask).where(
                RunTask.run_id.in_(ids), RunTask.status == "running"))).scalars().all()
            for rt in tasks:
                rt.status = "error"
                rt.finished_at = utcnow()
            await s.commit()

    async def stop_worker(self) -> None:
        self._running = False
        self._signal.set()
        if self._task:
            self._task.cancel()

    def enqueue(self, run_id: str) -> None:
        self._signal.set()

    async def _loop(self) -> None:
        while self._running:
            await self._signal.wait()
            self._signal.clear()
            while True:
                run_id = await self._next_queued()
                if run_id is None:
                    break
                control = RunControl(run_id=run_id)
                self._controls[run_id] = control
                try:
                    await execute_run(run_id, self.registry, self.hub, control)
                except Exception:
                    await self._mark_failed(run_id)
                finally:
                    self._controls.pop(run_id, None)
                    try:
                        from app.results.retention import prune
                        await prune()
                    except Exception:
                        pass

    async def _next_queued(self) -> str | None:
        async with db_engine.session_factory()() as s:
            row = (await s.execute(
                select(Run).where(Run.status == "queued").order_by(Run.queued_at).limit(1))).scalar_one_or_none()
            return row.id if row else None

    async def _mark_failed(self, run_id: str) -> None:
        async with db_engine.session_factory()() as s:
            run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
            if run and run.status == "running":
                run.status = "failed"
                run.finished_at = utcnow()
                await s.commit()

    # ── lifecycle actions ────────────────────────────────────────────────
    async def stop_run(self, run_id: str) -> None:
        control = self._controls.get(run_id)
        if control is not None:
            control.stop_event.set()
            if control.current_pid:
                kill_pid_group(control.current_pid)
        else:
            # queued but not started: finalize immediately
            async with db_engine.session_factory()() as s:
                run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
                if run and run.status == "queued":
                    run.status = "stopped"
                    run.finished_at = utcnow()
                    for rt in (await s.execute(select(RunTask).where(RunTask.run_id == run_id))).scalars():
                        if rt.status == "pending":
                            rt.status = "skipped"
                    await s.commit()

    async def skip_task(self, run_id: str, run_task_id: str) -> None:
        control = self._controls.get(run_id)
        if control is not None and control.current_run_task_id == run_task_id:
            control.skip_event.set()
            if control.current_pid:
                kill_pid_group(control.current_pid)
        else:
            async with db_engine.session_factory()() as s:
                rt = (await s.execute(select(RunTask).where(RunTask.id == run_task_id))).scalar_one_or_none()
                if rt and rt.status == "pending":
                    rt.status = "skipped"
                    rt.finished_at = utcnow()
                    await s.commit()

    async def restart_run(self, run_id: str) -> str:
        async with db_engine.session_factory()() as s:
            orig = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
            new_run = Run(id=new_id(), benchmark_id=orig.benchmark_id, agent_tool_id=orig.agent_tool_id,
                          setup_key=orig.setup_key, model=orig.model, status="queued",
                          config=dict(orig.config), task_timeout_seconds=orig.task_timeout_seconds,
                          queued_at=utcnow(), created_at=utcnow())
            s.add(new_run)
            await s.flush()
            orig_rts = (await s.execute(
                select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
            for rt in orig_rts:
                s.add(RunTask(run_id=new_run.id, task_id=rt.task_id, ordinal=rt.ordinal,
                              status="pending", timeout_seconds=rt.timeout_seconds))
            await s.commit()
            new_id_val = new_run.id
        self.enqueue(new_id_val)
        return new_id_val

    async def delete_run(self, run_id: str) -> bool:
        if run_id in self._controls:
            return False  # running: refuse
        import shutil

        from app.config import get_settings
        async with db_engine.session_factory()() as s:
            run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
            if run is None:
                return False
            if run.status == "running":
                return False
            await s.delete(run)
            await s.commit()
        tree = get_settings().outputs_dir / "runs" / run_id
        shutil.rmtree(tree, ignore_errors=True)
        return True
