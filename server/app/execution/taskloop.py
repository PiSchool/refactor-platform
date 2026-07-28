"""Platform-owned per-task loop. The benchmark contributes prompt + evaluation;
the setup shapes coordination; the agent owns launch/parse/cleanup. One
implementation for every benchmark / setup / agent tool.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import timezone
from pathlib import Path

from sqlalchemy import select

from app.catalog import tools
from app.catalog.loader import LoadedAgent, LoadedBenchmark, Registry
from app.catalog.sdk import EvalContext, SessionCtx, SessionInfo
from app.config import REPO_ROOT, get_settings
from app.db import engine as db_engine
from app.db.models import AgentSession, Benchmark, Run, RunTask, Task, TaskResult, new_id, utcnow
from app.evaluation import engine as evaluation
from app.catalog.templating import render
from app.execution import evaltool, workspace as ws
from app.execution.baseline import BaselineRejected, run_java_baseline
from app.execution.conformance import (
    SetupUnavailable,
    assess_setup,
    ensure_agent_compatible,
)
from app.execution.lsp import probe_server
from app.execution import wire
from app.execution.processes import kill_child_groups
from app.execution.pty_host import run_pty
from app.db.runtime import runtime_value
from app.execution.sandbox import build_user, chown_tree, demote_kwargs
from app.execution.setups import get_setup
from app.realtime.hub import Hub, TerminalChunk
from app.retrieval.chunking import repository_digest
from app.retrieval.errors import RetrievalCancelled, RetrievalUnavailable
from app.retrieval.service import RetrievalRequest, RetrievalService
from app.results.redaction import IncrementalTextRedactor, Redactor

# platform scaffolding injected into the workspace (never the agent's change)
_PLATFORM_ARTIFACTS = ("eval.sh", ".eval_count")
_EVAL_COMPLIANCE_PROMPT = """The required in-session self-check was not observed.
Run `bash eval.sh` now. If it reports a failure, fix the issue and re-run it
within the remaining attempt and time limits. Do not finish without invoking
the command at least once.
"""


@dataclass
class RunControl:
    run_id: str
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)
    skip_event: asyncio.Event = field(default_factory=asyncio.Event)
    current_run_task_id: str | None = None
    current_pid: int | None = None
    lsp_ready: set[str] = field(default_factory=set)

    def interrupted(self) -> bool:
        return self.stop_event.is_set() or self.skip_event.is_set()


class Interrupted(RuntimeError):
    """Raised when a stop or skip arrives before the agent has started.

    Preparing a task takes minutes: exporting a checkout, building the untouched
    project to prove its baseline is clean, indexing a repository. None of that
    used to observe the stop request, so Stop appeared to do nothing until the
    preparation had run to completion.
    """


logger = logging.getLogger(__name__)


async def _first_of(*events: asyncio.Event) -> None:
    """Return as soon as any of `events` is set."""
    waiters = [asyncio.create_task(event.wait()) for event in events]
    try:
        await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for waiter in waiters:
            waiter.cancel()


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
        if not await _still_pending(rt_id):
            continue  # skipped from the dashboard before its turn came up
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


async def _still_pending(rt_id: str) -> bool:
    """Honour a skip issued while the task was queued.

    The operator can skip any task of the active run, not just the one that is
    executing. Re-reading the row immediately before launch is what keeps that
    decision from being overwritten when the loop reaches the task.
    """
    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.id == rt_id))).scalar_one()
        return rt.status == "pending"


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
    safe_terminal_log = session_dir / ".terminal.redacted"
    terminal_redactor = IncrementalTextRedactor(
        Redactor.from_environment(private_paths=(
            session_dir,
            settings.outputs_dir,
            settings.data_dir,
            REPO_ROOT,
        ))
    )
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
    baseline_details = None
    terminal_offset = 0

    def publish_terminal(chunk: bytes) -> None:
        nonlocal terminal_offset
        if not chunk:
            return
        with safe_terminal_log.open("ab") as safe_log:
            safe_log.write(chunk)
        persisted = TerminalChunk(offset=terminal_offset, data=chunk)
        terminal_offset += len(chunk)
        hub.publish_threadsafe(f"terminal:{session_id}", "bytes", persisted)

    def on_bytes(chunk: bytes) -> None:
        publish_terminal(terminal_redactor.feed(chunk))

    def phase(text: str) -> None:
        """Announce a preparation step in the live terminal and honour a stop.

        Preparation is most of the wall clock on a Java task, and it used to be
        invisible: the dashboard said "No session yet" for minutes with nothing
        to read. Each step now names itself where the operator is already
        looking, and a stop request ends the task here instead of after the step.
        """
        on_bytes(f"[platform] {text}\r\n".encode())
        if control.stop_event.is_set():
            raise Interrupted("stopped")
        if control.skip_event.is_set():
            raise Interrupted("skipped")

    async def prepared(label: str, function, *args, **kwargs):
        """Run a blocking preparation step without deafening the stop request.

        The step runs in a worker thread, which cannot be cancelled, so the wait
        also watches the stop event. When it fires, the step's own children —
        each a session leader — are killed by process group, which is what ends
        a Maven or Gradle build together with its compiler and test JVMs.
        """
        phase(label)
        work = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
        watch = asyncio.create_task(_first_of(control.stop_event, control.skip_event))
        try:
            await asyncio.wait({work, watch}, return_when=asyncio.FIRST_COMPLETED)
            if work.done():
                return work.result()
            killed = kill_child_groups(exclude={control.current_pid} if control.current_pid else None)
            on_bytes(
                f"[platform] interrupted during {label}"
                f"{f'; killed {len(killed)} process group(s)' if killed else ''}\r\n".encode()
            )
            raise Interrupted("stopped" if control.stop_event.is_set() else "skipped")
        finally:
            watch.cancel()
            if not work.done():
                work.cancel()

    # The session row exists from the first second so the dashboard has
    # somewhere to show preparation, instead of "No session yet" while a
    # baseline build runs for minutes.
    async with db_engine.session_factory()() as s:
        s.add(AgentSession(id=session_id, run_task_id=rt_id, status="running",
                           terminal_path=str(terminal_log)))
        await s.commit()

    pw = build_user()
    try:
        if task_def is None:
            raise RuntimeError(f"task {task_row.task_key} not found in plugin")
        if not loaded_agent.available:
            raise SetupUnavailable(loaded_agent.unavailable_reason())
        ensure_agent_compatible(setup, loaded_agent.impl.capabilities)
        mismatch = wire.refusal(
            loaded_agent.manifest.name, loaded_agent.impl, settings.active_provider()
        )
        if mismatch:
            raise SetupUnavailable(mismatch)

        baseline = await prepared(
            f"preparing the workspace from {task_def.workspace.type} {task_def.workspace.source}",
            ws.prepare_sync, task_def, workspace_dir, loaded_bench.data_dir, settings.mirrors_dir,
        )
        baseline_timeout = min(
            int(timeout),
            settings.defaults.java_baseline_timeout_seconds,
        )
        baseline_result = await prepared(
            f"building the untouched project to check its baseline"
            f" (up to {baseline_timeout}s)",
            run_java_baseline,
            loaded_bench,
            task_def,
            workspace_dir,
            art,
            timeout_seconds=baseline_timeout,
        )
        if baseline_result is not None:
            baseline_details = baseline_result.details()
            if not baseline_result.ok:
                raise BaselineRejected(baseline_result)
        evaluation.seed_artifacts(loaded_bench, workspace_dir, task_def)
        if pw is not None:
            chown_tree(pw, art, pw.pw_dir)
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
            session_ctx.lsp_config = await prepared(
                f"starting the {task_def.language} language server",
                _resolve_lsp, registry, task_def.language, workspace_dir,
                run_as=demote_kwargs(pw),
                env={"HOME": pw.pw_dir} if pw is not None else None,
                probe=task_def.language not in control.lsp_ready,
            )
            control.lsp_ready.add(task_def.language)
        if setup.retrieval:
            retrieval_result = await prepared(
                "indexing the repository for retrieval",
                _prepare_retrieval, loaded_bench, task_def, workspace_dir, art,
                setup.retrieval, control,
            )
            session_ctx.extra["retrieval_context"] = retrieval_result.context
            session_ctx.extra["retrieval"] = {
                "indexKey": retrieval_result.index_key,
                "strategy": retrieval_result.strategy,
                "hits": len(retrieval_result.hits),
                "queries": len(retrieval_result.queries),
                "preInjected": retrieval_result.pre_injected,
                "provenancePath": str(retrieval_result.provenance_path),
                "invocationsPath": str(retrieval_result.invocations_path),
            }
            session_ctx.mcp_config = retrieval_result.mcp_config
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

        phase(f"starting {loaded_agent.manifest.name}")

        def on_pid(pid: int) -> None:
            control.current_pid = pid

        should_kill = lambda: control.stop_event.is_set() or control.skip_event.is_set()
        a0 = time.time()
        # Agent and evaluation build share one unprivileged identity, so neither
        # leaves scratch the other cannot clean (and no suite sees root).
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
        session_info = _parsed_session(loaded_agent, events_path, terminal_log)
        eval_results = evaltool.attempt_results(art)
        if (
            setup.eval_tool
            and not eval_results
            and not pty_result.timed_out
            and not pty_result.interrupted
            and not should_kill()
        ):
            remaining = max(0.0, float(timeout) - (time.time() - a0))
            compliance_prompt = art / "eval-compliance-prompt.md"
            compliance_prompt.write_text(_EVAL_COMPLIANCE_PROMPT, encoding="utf-8")
            resume_cmd = loaded_agent.impl.resume_command(session_ctx, compliance_prompt)
            if resume_cmd is not None and remaining > 0:
                marker = b"\r\n[platform] resuming session for mandatory self-check\r\n"
                with terminal_log.open("ab") as log:
                    log.write(marker)
                on_bytes(marker)
                pty_result = await run_pty(
                    resume_cmd, terminal_log, on_bytes, remaining,
                    on_pid=on_pid, should_kill=should_kill,
                    run_as=demote_kwargs(pw), append=True,
                )
                agent_seconds = time.time() - a0
                events_path = loaded_agent.impl.events_path(session_ctx)
                session_info = _parsed_session(loaded_agent, events_path, terminal_log)
                eval_results = evaltool.attempt_results(art)
        eval_attempts = len(eval_results)
        session_info.eval_iterations = max(session_info.eval_iterations, eval_attempts)
        session_info.eval_tool_invocations = max(session_info.eval_tool_invocations, eval_attempts)
        failed_self_checks = [row for row in eval_results if row.get("status") == "error"]
        if setup.eval_tool and failed_self_checks:
            error = str(failed_self_checks[0].get("error") or "unknown self-check error")
            raise SetupUnavailable(f"in-session self-check infrastructure failed: {error}")
        retrieval_meta = session_ctx.extra.get("retrieval", {})
        if retrieval_meta:
            recorded_calls = _jsonl_rows(Path(retrieval_meta["invocationsPath"]))
            session_info.retrieval_invocations = max(
                session_info.retrieval_invocations, recorded_calls
            )
            retrieval_meta["toolInvocations"] = session_info.retrieval_invocations
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
            details = {
                **outcome.details,
                **({"baseline": baseline_details} if baseline_details else {}),
            }
            status = "passed" if passed else "failed"
            metrics["evaluateSeconds"] = round(evaluate_seconds, 2)
    except Interrupted:
        status, reason = (
            ("stopped", "stopped") if control.stop_event.is_set() else ("skipped", "skipped")
        )
    except BaselineRejected as exc:
        status = "failed"
        reason = "baseline_failed"
        details = {"baseline": exc.result.details()}
    except SetupUnavailable as exc:
        status = "error"
        reason = "setup_unavailable"
        details = {"error": str(exc)[:2000], "setup": setup.key}
    except RetrievalCancelled as exc:
        if control.stop_event.is_set():
            status, reason = "stopped", "stopped"
        elif control.skip_event.is_set():
            status, reason = "skipped", "skipped"
        else:
            status, reason = "error", "retrieval_cancelled"
        details = {"error": str(exc)[:2000], "setup": setup.key}
    except RetrievalUnavailable as exc:
        status = "error"
        reason = "retrieval_unavailable"
        details = {"error": str(exc)[:2000], "setup": setup.key}
    except Exception as exc:  # always continue; record the failure
        status = "error"
        reason = "unknown"
        details = {"error": str(exc)[:2000]}

    publish_terminal(terminal_redactor.finalize())
    try:
        await _persist(rt_id, session_id, status, passed, reason, metrics, details,
                       session_info, diff_text, art, session_dir, loaded_agent,
                       session_ctx if task_def else None, agent_seconds, time.time() - t0)
    except Exception as exc:
        # Recording an outcome belongs to the task that produced it. When this
        # ran outside the failure boundary, one unrecordable result aborted the
        # whole run and left the row reading "running" with nothing behind it.
        logger.exception("run task %s: recording the outcome failed", rt_id)
        status, passed, reason = "error", False, "result_not_recorded"
        await _record_failure(rt_id, session_id, reason, str(exc)[:2000])
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
    server_root = str(Path(__file__).resolve().parents[2])
    inherited_pythonpath = os.getenv("PYTHONPATH", "").strip()
    env = {
        "HOME": str(config_dir),
        "TERM": "xterm-256color",
        # `uv` intentionally does not package app/. eval.sh runs from the task
        # workspace, so carry the canonical module root instead of depending on
        # the API process's current working directory.
        "PYTHONPATH": os.pathsep.join(
            part for part in (server_root, inherited_pythonpath) if part
        ),
        # FastEmbed must never discover or select a GPU in this release.
        "CUDA_VISIBLE_DEVICES": "",
    }
    # Provider access is resolved from the configured registry, so adding a
    # provider never means editing execution code: the adapter reads the
    # neutral RP_PROVIDER_* pair, and the provider's own variable names are
    # passed through for adapters that already speak them.
    from app.config import get_settings
    env.update(get_settings().provider_agent_env())
    return env


def _setup_exercised(setup, info, session_ctx=None) -> bool | None:
    """Whether the run actually used what its setup provides.

    None for S1: a baseline has no distinguishing mechanism to exercise. For the
    others this is the difference between "the agent had a language server" and
    "the agent used one" — the paper's ablation depends on the latter.
    """
    return assess_setup(setup, info, session_ctx).exercised


def _jsonl_rows(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def _resolve_lsp(
    registry: Registry, language: str, workspace: Path,
    run_as: dict | None = None, env: dict[str, str] | None = None,
    probe: bool = True,
) -> dict | None:
    loaded = registry.lsp_for(language)
    if loaded is None:
        raise SetupUnavailable(f"no LSP plugin is registered for language: {language}")
    ok, detail = loaded.impl.ensure()
    if not ok:
        raise SetupUnavailable(f"{language} LSP is unavailable: {detail}")
    config = loaded.impl.server_config(workspace)
    if probe:
        ok, detail = probe_server(config, workspace, run_as=run_as, env=env)
        if not ok:
            raise SetupUnavailable(f"{language} LSP failed readiness check: {detail}")
    return {"lspServers": {language: config}}


def _prepare_retrieval(
    loaded_bench, task_def, workspace: Path, artifacts: Path, strategy: str,
    control: RunControl,
):
    revision = task_def.workspace.ref
    if not revision:
        revision = repository_digest(workspace, task_def.language)
    service = RetrievalService.from_environment(get_settings().data_dir)
    return service.prepare(RetrievalRequest(
        benchmark=loaded_bench.manifest.key,
        source=task_def.workspace.source,
        revision=revision,
        language=task_def.language,
        strategy=strategy,
        instructions=task_def.instructions,
        params=task_def.params,
        workspace=workspace,
        artifacts_dir=artifacts,
        cancelled=lambda: control.stop_event.is_set() or control.skip_event.is_set(),
    ))


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


#: A file path inside a task's own instructions: `requests/utils.py`, quoted or
#: not. Deliberately narrow — a bare word or a sentence is not a path.
_PATH_IN_TEXT = re.compile(r"[\w.-]+(?:/[\w.-]+)+\.\w{1,5}")


def _task_field(task_def, reference: str) -> str:
    """Read `params.<name>` off a task. Anything else is the literal value."""
    if reference.startswith("params."):
        return str(task_def.params.get(reference[len("params."):]) or "")
    return reference


def _source_root_line(session_ctx, task_def, prompt_spec) -> str:
    """One line resolving where the task's own paths live, when they differ.

    RefactorBench's instructions were written against the upstream project, so
    they name `requests/utils.py` in a checkout that keeps that file at
    `src/requests/utils.py`. The task records the directory; until now only the
    scoring step read it, and every agent had to discover the difference: in one
    recorded run four of the agent's turns were failed reads of paths that do not
    exist. The instruction text is left exactly as the dataset wrote it and the
    difference is stated instead, with an example taken from the task itself.
    """
    reference = getattr(prompt_spec, "pathsRelativeTo", "") if prompt_spec else ""
    if not reference:
        return ""
    root = _task_field(task_def, reference).strip("/")
    if not root or not (session_ctx.workspace / root).is_dir():
        return ""
    for candidate in _PATH_IN_TEXT.findall(task_def.instructions or ""):
        if (session_ctx.workspace / candidate).exists():
            return ""
        if (session_ctx.workspace / root / candidate).is_file():
            return (f"This task writes source paths relative to `{root}/`: "
                    f"`{candidate}` is `{root}/{candidate}`.")
    return f"This task writes source paths relative to `{root}/`."


def _workspace_preamble(session_ctx, task_def=None, prompt_spec=None) -> str:
    """Where the code is, stated once, for every benchmark and every agent.

    A task's instructions name files relative to the repository root, and the
    agent is started with that root as its working directory — but nothing said
    so. In one recorded run the agent read the absolute path of its prompt file,
    inferred a sibling `workspace/` directory, and spent four of its turns
    reading `workspace/requests/utils.py`, `requests/utils.py` and
    `/requests/utils.py` before finding the file. The study's harness did not
    need this line because it never showed the agent an absolute path; this one
    does, so it states the root.
    """
    text = (
        f"Repository root: {session_ctx.workspace}\n"
        f"That is your working directory. Every file path in this task is "
        f"relative to it."
    )
    if task_def is not None:
        note = _source_root_line(session_ctx, task_def, prompt_spec)
        if note:
            text = f"{text}\n{note}"
    return text


def _build_prompt(loaded_bench, task_def, session_ctx, setup) -> str:
    tmpl = loaded_bench.manifest.prompt
    prompt = loaded_bench.hooks.build_prompt(task_def, session_ctx)
    if prompt is None:
        if tmpl is None:
            prompt = task_def.instructions
        else:
            prompt = render(_template_text(loaded_bench, tmpl.template), task_def)
    preamble = _workspace_preamble(session_ctx, task_def, tmpl)
    prompt = f"{preamble}\n\n{prompt.lstrip()}"
    retrieval_context = session_ctx.extra.get("retrieval_context", "")
    if retrieval_context:
        prompt = f"{prompt}\n\n{retrieval_context.rstrip()}\n"
    if setup.prompt_block:
        prompt = f"{prompt}\n\n{setup.prompt_block}\n"
    return prompt


def _parsed_session(loaded_agent: LoadedAgent, events_path, terminal_log) -> SessionInfo:
    """The adapter's reading of its own session, checked against the contract.

    An adapter that returns something else is a plugin defect, and it has to
    surface as this task's failure with the plugin named. Left unchecked it
    fails later, in code that has no idea which plugin produced the value.
    """
    info = loaded_agent.impl.parse_session(events_path, terminal_log)
    if not isinstance(info, SessionInfo):
        raise TypeError(
            f"agent plugin {loaded_agent.manifest.key!r} returned "
            f"{type(info).__name__} from parse_session; expected SessionInfo"
        )
    return info


async def _record_failure(rt_id: str, session_id: str, reason: str, error: str) -> None:
    """Close a task row when its full result could not be written."""
    async with db_engine.session_factory()() as s:
        rt = (await s.execute(select(RunTask).where(RunTask.id == rt_id))).scalar_one_or_none()
        if rt is None:
            return
        rt.status = "error"
        rt.finished_at = utcnow()
        rt.workspace_path = None
        sess = (await s.execute(
            select(AgentSession).where(AgentSession.id == session_id))).scalar_one_or_none()
        if sess is not None:
            sess.status = "ended"
            sess.finished_at = utcnow()
        existing = (await s.execute(
            select(TaskResult).where(TaskResult.run_task_id == rt_id))).scalar_one_or_none()
        if existing is None:
            s.add(TaskResult(run_task_id=rt_id, passed=False, reason=reason,
                             details={"error": error}))
        await s.commit()


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
        # Asked of the installed command, not declared in the manifest: a
        # hand-written version drifts from the CLI that produced this diff.
        "agentVersion": tools.command_state(loaded_agent.manifest)["version"],
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
        retrieval_meta = session_ctx.extra.get("retrieval", {}) if session_ctx else {}
        eval_attempts = evaltool.completed_attempts(art)
        assessment = assess_setup(
            session_ctx.setup, session_info, session_ctx, eval_attempts=eval_attempts,
        ) if session_ctx else None
        setup_unavailable = reason in {"setup_unavailable", "retrieval_unavailable"}
        metrics = {
            **metrics,
            "tokensCacheRead": session_info.tokens_cache_read,
            "tokensReasoning": session_info.tokens_reasoning,
            "contextTokens": session_info.context_tokens,
            "compactionCount": session_info.compaction_count,
            "contextOverflowCount": session_info.context_overflow_count,
            "evalIterations": session_info.eval_iterations,
            "evalAttempts": eval_attempts,
            # Did the setup's mechanism actually get exercised? A setup offers a
            # capability and asks for it in the prompt; the model may ignore both,
            # in which case an "S1-LSP" run is indistinguishable from plain S1.
            "lspActions": session_info.lsp_actions,
            "subagentInvocations": session_info.subagent_invocations,
            "evalToolInvocations": session_info.eval_tool_invocations,
            "retrievalInvocations": session_info.retrieval_invocations,
            "retrievalPreInjected": bool(retrieval_meta.get("preInjected")),
            "retrievalHits": int(retrieval_meta.get("hits", 0)),
            "retrievalQueries": int(retrieval_meta.get("queries", 0)),
            "retrievalStrategy": retrieval_meta.get("strategy", ""),
            "retrievalIndexKey": retrieval_meta.get("indexKey", ""),
            "setupExercised": False if setup_unavailable and assessment else (
                assessment.exercised if assessment else None
            ),
            "setupCompliance": "setup_unavailable" if setup_unavailable else (
                assessment.status if assessment else "setup_unavailable"
            ),
            "setupExpected": list(assessment.expected) if assessment else [],
            "setupUnexpected": list(assessment.unexpected) if assessment else [],
        }
        if retrieval_meta:
            details = {**details, "retrieval": retrieval_meta}
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
