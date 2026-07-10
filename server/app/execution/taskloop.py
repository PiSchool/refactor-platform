"""Platform-owned per-task loop. The benchmark contributes prompt + evaluation;
the setup shapes coordination; the agent owns launch/parse/cleanup. One
implementation for every benchmark / setup / agent tool.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import timezone
from pathlib import Path

from sqlalchemy import select

from app.catalog.loader import LoadedAgent, LoadedBenchmark, Registry
from app.catalog.sdk import EvalContext, SessionCtx, SessionInfo
from app.config import get_settings
from app.db import engine as db_engine
from app.db.models import AgentSession, Benchmark, Run, RunTask, Task, TaskResult, new_id, utcnow
from app.evaluation import engine as evaluation
from app.evaluation.render import render
from app.execution import evaltool, workspace as ws
from app.execution.pty_host import run_pty
from app.db.runtime import runtime_value
from app.execution.sandbox import build_user, chown_tree, demote_kwargs
from app.execution.setups import get_setup
from app.realtime.hub import Hub

# platform scaffolding injected into the workspace (never the agent's change)
_PLATFORM_ARTIFACTS = ("eval.sh", ".eval_count")


@dataclass
class RunControl:
    run_id: str
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)
    skip_event: asyncio.Event = field(default_factory=asyncio.Event)
    current_run_task_id: str | None = None
    current_pid: int | None = None


def _iso(dt) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


async def execute_run(run_id: str, registry: Registry, hub: Hub, control: RunControl) -> None:
    settings = get_settings()
    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
        run.status = "running"
        run.started_at = utcnow()
        bench_row = (await s.execute(select(Benchmark).where(Benchmark.id == run.benchmark_id))).scalar_one()
        rts = (await s.execute(
            select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.ordinal))).scalars().all()
        rt_ids = [rt.id for rt in rts]
        await s.commit()

    loaded_bench = registry.benchmarks[bench_row.key]
    from app.db.models import AgentTool
    async with db_engine.session_factory()() as s:
        tool_row = (await s.execute(select(AgentTool).where(AgentTool.id == run.agent_tool_id))).scalar_one()
    loaded_agent = registry.agents[tool_row.key]
    setup = get_setup(run.setup_key)

    hub.publish(f"run:{run_id}", "status", {"runStatus": "running"})

    final_status = "completed"
    for idx, rt_id in enumerate(rt_ids):
        if control.stop_event.is_set():
            await _finalize_remaining(rt_ids[idx:], hub, run_id)
            final_status = "stopped"
            break
        outcome_status = await _run_one_task(
            rt_id, idx, len(rt_ids), run, loaded_bench, loaded_agent, setup, registry, hub, control, settings)
        if outcome_status == "stopped":
            await _finalize_remaining(rt_ids[idx + 1:], hub, run_id)
            final_status = "stopped"
            break

    async with db_engine.session_factory()() as s:
        run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
        run.status = final_status
        run.finished_at = utcnow()
        await s.commit()
    hub.publish(f"run:{run_id}", "status", {"runStatus": final_status})


async def _finalize_remaining(rt_ids: list[str], hub: Hub, run_id: str) -> None:
    async with db_engine.session_factory()() as s:
        for rt_id in rt_ids:
            rt = (await s.execute(select(RunTask).where(RunTask.id == rt_id))).scalar_one()
            if rt.status == "pending":
                rt.status = "skipped"
                rt.finished_at = utcnow()
        await s.commit()


async def _run_one_task(rt_id, idx, total, run, loaded_bench: LoadedBenchmark,
                        loaded_agent: LoadedAgent, setup, registry, hub: Hub,
                        control: RunControl, settings) -> str:
    control.current_run_task_id = rt_id
    control.current_pid = None
    control.skip_event.clear()
    session_id = new_id()
    t0 = time.time()

    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.id == rt_id))).scalar_one()
        task_row = (await s.execute(select(Task).where(Task.id == rt.task_id))).scalar_one()
        rt.status = "running"
        rt.started_at = utcnow()
        timeout = rt.timeout_seconds
        await s.commit()

    task_def = next((t for t in loaded_bench.tasks if t.task_key == task_row.task_key), None)
    art = settings.outputs_dir / "runs" / run.id / "tasks" / rt_id
    workspace_dir = art / "workspace"
    session_dir = art / "agent-session" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    terminal_log = session_dir / "terminal.log"
    config_dir = session_dir / "home"
    config_dir.mkdir(parents=True, exist_ok=True)

    hub.publish(f"run:{run.id}", "status",
                {"runStatus": "running", "currentTaskKey": task_row.task_key,
                 "progress": {"done": idx, "total": total}})

    status = "error"
    session_info = SessionInfo()
    reason = "unknown"
    passed = False
    metrics: dict = {}
    details: dict = {}
    diff_text = ""
    agent_seconds = 0.0
    session_ctx = None
    try:
        if task_def is None:
            raise RuntimeError(f"task {task_row.task_key} not found in plugin")

        baseline = await ws.prepare(task_def, workspace_dir, loaded_bench.data_dir, settings.mirrors_dir)
        evaluation.seed_artifacts(loaded_bench, workspace_dir, task_def)
        async with db_engine.session_factory()() as s:  # expose live workspace to eval.sh
            rt = (await s.execute(select(RunTask).where(RunTask.id == rt_id))).scalar_one()
            rt.workspace_path = str(workspace_dir)
            await s.commit()

        # prompt: benchmark hook or template, + setup prompt_block
        session_ctx = SessionCtx(
            run_id=run.id, run_task_id=rt_id, session_id=session_id, task=task_def,
            workspace=workspace_dir, artifacts_dir=art, prompt_path=art / "prompt.md",
            config_dir=config_dir, model=run.model, setup=setup,
            requested_env=_agent_env(run, config_dir),
            extra={**run.config.get("extra", {}),
                   # plugin hooks read their templates from here first
                   "prompts_dir": str(settings.prompt_overrides_dir / loaded_bench.manifest.key)})
        if setup.lsp:
            session_ctx.lsp_config = _resolve_lsp(registry, task_def.language, workspace_dir)
        prompt = _build_prompt(loaded_bench, task_def, session_ctx, setup)
        (art / "prompt.md").write_text(prompt, encoding="utf-8")

        if setup.eval_tool:
            evaltool.install(rt_id, workspace_dir,
                             int(run.config.get("eval_tool_max_attempts",
                                                settings.defaults.eval_tool_max_attempts)))

        loaded_agent.impl.prepare(session_ctx)
        cmd = loaded_agent.impl.command(session_ctx)

        # Scaffolding written after the baseline commit would otherwise be swept
        # into the agent's diff by `git add -A`.
        ws.ignore_paths(workspace_dir, [*_PLATFORM_ARTIFACTS,
                                        *loaded_agent.impl.workspace_artifacts])

        async with db_engine.session_factory()() as s:
            s.add(AgentSession(id=session_id, run_task_id=rt_id, status="running",
                               terminal_path=str(terminal_log)))
            await s.commit()

        def on_pid(pid: int) -> None:
            control.current_pid = pid

        def on_bytes(chunk: bytes) -> None:
            hub.publish_threadsafe(f"terminal:{session_id}", "bytes", chunk)

        should_kill = lambda: control.stop_event.is_set() or control.skip_event.is_set()
        a0 = time.time()
        # Agent and evaluation build share one unprivileged identity, so neither
        # leaves scratch the other cannot clean (and no suite sees root).
        pw = build_user()
        if pw is not None:
            chown_tree(pw, art, pw.pw_dir)
        # The agent names its own events file (a uuid dir), so the path only
        # exists once it starts. Publish it as soon as it appears, otherwise the
        # live Events view has nothing to read until the run is over.
        tracker = asyncio.create_task(_track_events_path(session_id, session_ctx, loaded_agent))
        try:
            pty_result = await run_pty(cmd, terminal_log, on_bytes, float(timeout),
                                       on_pid=on_pid, should_kill=should_kill,
                                       run_as=demote_kwargs(pw))
        finally:
            tracker.cancel()
        agent_seconds = time.time() - a0

        events_path = loaded_agent.impl.events_path(session_ctx)
        session_info = loaded_agent.impl.parse_session(events_path, terminal_log)
        loaded_agent.impl.cleanup(session_ctx)

        (art / "response.md").write_text(session_info.response_text or "", encoding="utf-8")
        if session_info.readable_transcript:
            (session_dir / "transcript.txt").write_text(session_info.readable_transcript, encoding="utf-8")

        # git + evaluation are blocking and can run for minutes (mvn, pytest,
        # RefactoringMiner). Running them on the event loop froze the whole ASGI
        # server, so the UI's requests died with "socket hang up".
        diff_text = await asyncio.to_thread(ws.capture_diff, workspace_dir)
        (art / "diff.patch").write_text(diff_text, encoding="utf-8")
        await asyncio.to_thread(_write_meta, art, task_def, baseline, workspace_dir,
                                run, loaded_agent, setup, session_info)

        if control.stop_event.is_set():
            status = "stopped"
            reason = "stopped"
        elif control.skip_event.is_set():
            status = "skipped"
            reason = "skipped"
        elif pty_result.timed_out:
            status = "timed_out"
            reason = "timed_out"
        else:
            e0 = time.time()
            # Operator edits to the pipeline (Settings) are read here, in async
            # context, then handed to the worker thread.
            eval_override = await runtime_value(f"evaluation:{loaded_bench.manifest.key}", None)
            outcome = await asyncio.to_thread(
                _evaluate, loaded_bench, task_def, workspace_dir, art, session_info,
                diff_text, eval_override)
            evaluate_seconds = time.time() - e0
            passed = outcome.passed
            reason = outcome.reason
            metrics = outcome.metrics
            details = outcome.details
            status = "passed" if passed else "failed"
            metrics["evaluateSeconds"] = round(evaluate_seconds, 2)
    except Exception as exc:  # always continue; record the failure
        status = "error"
        reason = "unknown"
        details = {"error": str(exc)[:2000]}

    await _persist(rt_id, session_id, status, passed, reason, metrics, details,
                   session_info, diff_text, art, session_dir, loaded_agent, session_ctx if task_def else None,
                   agent_seconds, time.time() - t0)
    hub.publish(f"run:{run.id}", "task",
                {"taskKey": task_row.task_key, "status": status, "passed": passed, "reason": reason})

    # The checkout is the run's primary evidence — browsing it after the fact is
    # how a reviewer inspects what the agent actually produced. Operators can
    # trade that for disk (a guava checkout is hundreds of MB).
    if not await runtime_value("keepWorkspace", True):
        import shutil
        await asyncio.to_thread(shutil.rmtree, workspace_dir, True)
    return "stopped" if status == "stopped" else status


def _agent_env(run, config_dir: Path) -> dict[str, str]:
    import os
    env = {"HOME": str(config_dir), "TERM": "xterm-256color"}
    for k in ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "OPENROUTER_MODEL", "COPILOT_GITHUB_TOKEN"):
        v = os.getenv(k)
        if v:
            env[k] = v
    return env


def _resolve_lsp(registry: Registry, language: str, workspace: Path) -> dict | None:
    loaded = registry.lsp_for(language)
    if loaded is None:
        return None
    ok, _ = loaded.impl.ensure()
    if not ok:
        return None
    return {"lspServers": {language: loaded.impl.server_config(workspace)}}


async def _track_events_path(session_id: str, session_ctx, loaded_agent) -> None:
    """Persist the agent's events file as soon as the adapter can locate it.
    Only the plugin knows the layout; the platform just stores the result."""
    while True:
        try:
            path = loaded_agent.impl.events_path(session_ctx)
        except Exception:
            path = None
        if path:
            async with db_engine.session_factory()() as s:
                sess = (await s.execute(select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
                if sess is not None and not sess.events_path:
                    sess.events_path = str(path)
                    await s.commit()
            return
        await asyncio.sleep(2)


def _template_text(loaded_bench, relpath: str) -> str:
    """Operator overrides (data volume) win over the plugin's shipped default."""
    override = get_settings().prompt_overrides_dir / loaded_bench.manifest.key / Path(relpath).name
    path = override if override.is_file() else loaded_bench.plugin_dir / relpath
    return path.read_text(encoding="utf-8")


def _build_prompt(loaded_bench, task_def, session_ctx, setup) -> str:
    prompt = loaded_bench.hooks.build_prompt(task_def, session_ctx)
    if prompt is None:
        tmpl = loaded_bench.manifest.prompt
        if tmpl is None:
            prompt = task_def.instructions
        else:
            prompt = render(_template_text(loaded_bench, tmpl.template), task_def)
    if setup.prompt_block:
        prompt = f"{prompt}\n\n{setup.prompt_block}\n"
    return prompt


def _evaluate(loaded_bench, task_def, workspace, art, session_info, diff_text, override=None):
    ctx = EvalContext(task=task_def, workspace=workspace, artifacts_dir=art,
                      data_root=loaded_bench.data_dir, session=session_info,
                      diff_text=diff_text, advisory=False)
    return evaluation.evaluate(loaded_bench, ctx, override)


def _write_meta(art, task_def, baseline, workspace, run, loaded_agent, setup, session_info) -> None:
    meta = {
        "source": task_def.workspace.source,
        "ref": task_def.workspace.ref,
        "baseline": baseline,
        "changedFiles": ws.changed_files(workspace),
        "model": run.model,
        "agentKey": loaded_agent.manifest.key,
        "agentVersion": loaded_agent.manifest.version,
        "setupKey": setup.key,
        "flags": sorted(session_info.flags),
    }
    (art / "workspace_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


async def _persist(rt_id, session_id, status, passed, reason, metrics, details, session_info,
                   diff_text, art, session_dir, loaded_agent, session_ctx, agent_seconds, total_seconds):
    events_rel = None
    if session_ctx is not None:
        ep = loaded_agent.impl.events_path(session_ctx)
        events_rel = str(ep) if ep and Path(ep).is_file() else None
    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.id == rt_id))).scalar_one()
        rt.status = status
        rt.finished_at = utcnow()
        rt.workspace_path = None
        sess = (await s.execute(select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
        if sess is not None:
            sess.status = "killed" if status in ("stopped", "timed_out") else "ended"
            sess.finished_at = utcnow()
            sess.events_path = events_rel
        # session-level counters a reviewer needs: what the agent spent, and
        # whether it ran out of room to think.
        metrics = {
            **metrics,
            "tokensCacheRead": session_info.tokens_cache_read,
            "tokensReasoning": session_info.tokens_reasoning,
            "contextTokens": session_info.context_tokens,
            "compactionCount": session_info.compaction_count,
            "contextOverflowCount": session_info.context_overflow_count,
            "evalIterations": session_info.eval_iterations,
        }
        s.add(TaskResult(
            run_task_id=rt_id, passed=passed, reason=reason,
            agent_seconds=round(agent_seconds, 2),
            evaluate_seconds=round(metrics.get("evaluateSeconds", 0.0), 2),
            duration_seconds=round(total_seconds, 2),
            tokens_input=session_info.tokens_input, tokens_output=session_info.tokens_output,
            model=session_info.model, metrics=metrics, details=details,
            prompt_path=str(art / "prompt.md"), response_path=str(art / "response.md"),
            diff_path=str(art / "diff.patch"), terminal_path=str(session_dir / "terminal.log"),
            events_path=events_rel, eval_dir=str(art / "eval")))
        await s.commit()
