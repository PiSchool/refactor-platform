from __future__ import annotations

from dataclasses import replace
import json
import math
import os
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import func, select

from tests.helpers import FIXTURES, make_run, seed_catalog

@pytest.fixture()
async def exported_run(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    from app import config
    from app.db import engine as db_engine
    from app.db.models import AgentSession, Run, RunTask, TaskResult, utcnow
    from app.results.export import build_zip

    config.get_settings.cache_clear()
    await seed_catalog()
    source_run_id = await make_run(task_keys=["fixture-0001"])
    async with db_engine.session_factory()() as session:
        run = (await session.execute(
            select(Run).where(Run.id == source_run_id)
        )).scalar_one()
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == source_run_id)
        )).scalar_one()
        now = utcnow()
        run.status = "completed"
        run.started_at = now
        run.finished_at = now
        run_task.status = "passed"
        run_task.started_at = now
        run_task.finished_at = now

        task_root = (
            config.get_settings().outputs_dir / "runs" / source_run_id
            / "tasks" / run_task.id
        )
        session_id = "source-session"
        session_root = task_root / "agent-session" / session_id
        session_root.mkdir(parents=True)
        (task_root / "prompt.md").write_text("prompt\n", encoding="utf-8")
        (task_root / "response.md").write_text("response\n", encoding="utf-8")
        (task_root / "diff.patch").write_text("diff --git a/a b/a\n", encoding="utf-8")
        (task_root / "workspace_meta.json").write_text(
            json.dumps({"baseline": "abc123"}), encoding="utf-8",
        )
        (session_root / "terminal.log").write_text("terminal\n", encoding="utf-8")
        (session_root / "transcript.txt").write_text("transcript\n", encoding="utf-8")
        events = session_root / "events.jsonl"
        events.write_text('{"type":"session.end"}\n', encoding="utf-8")

        agent_session = AgentSession(
            id=session_id,
            run_task_id=run_task.id,
            status="ended",
            terminal_path=str(session_root / "terminal.log"),
            events_path=str(events),
            started_at=now,
            finished_at=now,
        )
        result = TaskResult(
            run_task_id=run_task.id,
            passed=True,
            reason="passed",
            agent_seconds=1.0,
            evaluate_seconds=2.0,
            duration_seconds=3.0,
            tokens_input=4,
            tokens_output=5,
            model="stub-model",
            metrics={"score": 1},
            details={"stage": "done"},
            prompt_path=str(task_root / "prompt.md"),
            response_path=str(task_root / "response.md"),
            diff_path=str(task_root / "diff.patch"),
            terminal_path=str(session_root / "terminal.log"),
            events_path=str(events),
        )
        session.add_all([agent_session, result])
        await session.commit()
        source_task_id = run_task.id

    archive_path = await build_zip(source_run_id)
    assert archive_path is not None
    return {
        "archive": archive_path,
        "run_id": source_run_id,
        "task_id": source_task_id,
        "session_id": session_id,
    }


def _rewrite_archive(source: Path, destination: Path, mutate) -> Path:
    with zipfile.ZipFile(source) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    mutate(entries)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return destination


@pytest.mark.asyncio
async def test_round_trip_uses_fresh_ids_and_restores_evidence(exported_run):
    from app import config
    from app.db import engine as db_engine
    from app.db.models import AgentSession, Run, RunTask, TaskResult
    from app.results.import_run import import_archive

    new_run_id = await import_archive(exported_run["archive"])
    assert new_run_id != exported_run["run_id"]

    async with db_engine.session_factory()() as session:
        run = (await session.execute(select(Run).where(Run.id == new_run_id))).scalar_one()
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == new_run_id)
        )).scalar_one()
        result = (await session.execute(
            select(TaskResult).where(TaskResult.run_task_id == run_task.id)
        )).scalar_one()
        agent_session = (await session.execute(
            select(AgentSession).where(AgentSession.run_task_id == run_task.id)
        )).scalar_one()

    assert run_task.id != exported_run["task_id"]
    assert agent_session.id != exported_run["session_id"]
    assert set(run.config["import"]) == {"format", "sourceRunId", "createdAt"}
    assert run.config["import"]["format"] == "refactor-platform-run"
    assert run.config["import"]["sourceRunId"] == exported_run["run_id"]
    root = config.get_settings().outputs_dir / "runs" / new_run_id / "tasks" / run_task.id
    assert (root / "prompt.md").read_text(encoding="utf-8") == "prompt\n"
    assert (root / "agent-session" / agent_session.id / "terminal.log").is_file()
    for pointer in (result.prompt_path, result.response_path, result.diff_path,
                    result.terminal_path, result.events_path,
                    agent_session.terminal_path, agent_session.events_path):
        assert pointer and Path(pointer).is_file()
        assert str(pointer).startswith(str(root))


@pytest.mark.asyncio
async def test_import_accepts_known_archive_only_setup(exported_run, tmp_path):
    from app.db import engine as db_engine
    from app.db.models import Run
    from app.results.import_run import import_archive

    def use_archived_setup(entries: dict[str, bytes]) -> None:
        summary = json.loads(entries["summary.json"])
        summary["run"]["setup"] = {"key": "s3_cao", "name": "CAO multi-agent"}
        entries["summary.json"] = json.dumps(summary).encode("utf-8")
        manifest = json.loads(entries["manifest.json"])
        manifest["setup"] = {
            "key": "s3_cao",
            "name": "CAO multi-agent",
        }
        entries["manifest.json"] = json.dumps(manifest).encode("utf-8")

    archive = _rewrite_archive(
        exported_run["archive"],
        tmp_path / "archive-only.zip",
        use_archived_setup,
    )
    run_id = await import_archive(archive)
    async with db_engine.session_factory()() as session:
        run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one()

    assert run.setup_key == "s3_cao"
    assert run.config["import"]["sourceRunId"] == exported_run["run_id"]


@pytest.mark.asyncio
async def test_versioned_manifest_is_rejected_before_extraction(
    exported_run, tmp_path,
):
    from app.results.import_run import ImportRejected, import_archive

    def mutate(entries):
        manifest = json.loads(entries["manifest.json"])
        manifest["version"] = 2
        entries["manifest.json"] = json.dumps(manifest).encode()

    archive = _rewrite_archive(exported_run["archive"], tmp_path / "versioned.zip", mutate)
    with pytest.raises(ImportRejected, match="unexpected.*version"):
        await import_archive(archive)


@pytest.mark.asyncio
async def test_commit_failure_rolls_back_rows_and_files(exported_run, monkeypatch):
    from app import config
    from app.db import engine as db_engine
    from app.db.models import Run
    from app.results import import_run

    async with db_engine.session_factory()() as session:
        before = (await session.execute(select(func.count()).select_from(Run))).scalar_one()
    runs_dir = config.get_settings().outputs_dir / "runs"
    directories_before = {path.name for path in runs_dir.iterdir()}

    async def fail_commit(_session):
        raise RuntimeError("injected commit failure")

    monkeypatch.setattr(import_run, "_commit_import", fail_commit)
    with pytest.raises(RuntimeError, match="injected"):
        await import_run.import_archive(exported_run["archive"])

    async with db_engine.session_factory()() as session:
        after = (await session.execute(select(func.count()).select_from(Run))).scalar_one()
    assert after == before
    assert {path.name for path in runs_dir.iterdir()} == directories_before
    assert not list(runs_dir.glob(".importing-*"))


def _mutate_json_documents(entries, mutate) -> None:
    manifest = json.loads(entries["manifest.json"])
    summary = json.loads(entries["summary.json"])
    mutate(manifest, summary)
    entries["manifest.json"] = json.dumps(manifest).encode()
    entries["summary.json"] = json.dumps(summary).encode()


def _bad_hash(manifest, _summary):
    manifest["artifacts"][0]["sha256"] = "0" * 64


def _active_run(manifest, summary):
    manifest["status"] = "running"
    summary["run"]["status"] = "running"


def _source_path(_manifest, summary):
    summary["run"]["config"]["source"] = "/home/reviewer/private"


def _unknown_benchmark(manifest, summary):
    manifest["benchmark"]["key"] = "missing-benchmark"
    summary["run"]["benchmark"]["key"] = "missing-benchmark"


def _unknown_agent(manifest, summary):
    manifest["agentTool"]["key"] = "missing-agent"
    summary["run"]["agentTool"]["key"] = "missing-agent"


def _unknown_setup(manifest, summary):
    manifest["setup"]["key"] = "missing-setup"
    summary["run"]["setup"]["key"] = "missing-setup"


def _unsupported_setup(manifest, summary):
    manifest["setup"]["key"] = "s3"
    summary["run"]["setup"]["key"] = "s3"


def _unknown_task(_manifest, summary):
    summary["tasks"][0]["taskKey"] = "missing-task"


def _duplicate_task(manifest, summary):
    summary["tasks"].append(dict(summary["tasks"][0]))
    manifest["taskCount"] = 2


def _active_task(_manifest, summary):
    summary["tasks"][0]["status"] = "running"


def _active_session(_manifest, summary):
    summary["tasks"][0]["session"]["status"] = "running"


def _negative_ordinal(_manifest, summary):
    summary["tasks"][0]["ordinal"] = -1


def _invalid_datetime(_manifest, summary):
    summary["tasks"][0]["finishedAt"] = "not-a-date"


def _non_finite_duration(_manifest, summary):
    summary["tasks"][0]["result"]["durationSeconds"] = math.nan


def _non_object_config(_manifest, summary):
    summary["run"]["config"] = []


def _hidden_workspace_path(_manifest, summary):
    summary["tasks"][0]["workspacePath"] = "relative/private"


def _coerced_manifest_count(manifest, _summary):
    manifest["taskCount"] = str(manifest["taskCount"])


@pytest.mark.parametrize("mutation", [
    _bad_hash,
    _active_run,
    _source_path,
    _unknown_benchmark,
    _unknown_agent,
    _unknown_setup,
    _unsupported_setup,
    _unknown_task,
    _duplicate_task,
    _active_task,
    _active_session,
    _negative_ordinal,
    _invalid_datetime,
    _non_finite_duration,
    _non_object_config,
    _hidden_workspace_path,
    _coerced_manifest_count,
], ids=lambda mutation: mutation.__name__)
@pytest.mark.asyncio
async def test_untrusted_metadata_is_rejected_without_partial_state(
    exported_run, tmp_path, mutation,
):
    from app import config
    from app.results.archive_safety import ArchiveSafetyError
    from app.results.import_run import ImportRejected, import_archive

    runs_dir = config.get_settings().outputs_dir / "runs"
    before = {path.name for path in runs_dir.iterdir()}

    def mutate(entries):
        _mutate_json_documents(entries, mutation)

    archive = _rewrite_archive(
        exported_run["archive"], tmp_path / f"{mutation.__name__}.zip", mutate,
    )
    with pytest.raises((ImportRejected, ArchiveSafetyError)):
        await import_archive(archive)

    assert {path.name for path in runs_dir.iterdir()} == before
    assert not list(runs_dir.glob(".importing-*"))


@pytest.mark.asyncio
async def test_manifest_is_required(exported_run, tmp_path):
    from app.results.archive_safety import ArchiveSafetyError
    from app.results.import_run import ImportRejected, import_archive

    archive = _rewrite_archive(
        exported_run["archive"], tmp_path / "missing-manifest.zip",
        lambda entries: entries.pop("manifest.json"),
    )
    with pytest.raises((ImportRejected, ArchiveSafetyError), match="manifest.json"):
        await import_archive(archive)


@pytest.mark.asyncio
async def test_manifest_nested_unknown_fields_are_rejected(exported_run, tmp_path):
    from app.results.import_run import ImportRejected, import_archive

    def mutate(entries):
        _mutate_json_documents(
            entries,
            lambda manifest, _summary: manifest["benchmark"].update({"privatePath": "relative"}),
        )

    archive = _rewrite_archive(exported_run["archive"], tmp_path / "extra.zip", mutate)
    with pytest.raises(ImportRejected, match="unexpected"):
        await import_archive(archive)


@pytest.mark.asyncio
async def test_malformed_and_oversized_json_are_rejected(exported_run, tmp_path):
    from app import config
    from app.results.archive_safety import ArchiveSafetyError
    from app.results.import_run import ImportRejected, import_archive

    malformed = _rewrite_archive(
        exported_run["archive"], tmp_path / "malformed.zip",
        lambda entries: entries.__setitem__("summary.json", b"{not json"),
    )
    with pytest.raises(ImportRejected, match="malformed"):
        await import_archive(malformed)

    limits = replace(config.get_settings().import_limits, max_json_bytes=64)
    with pytest.raises(ArchiveSafetyError):
        await import_archive(exported_run["archive"], limits=limits)


@pytest.mark.asyncio
async def test_unlisted_and_traversal_members_are_rejected(exported_run, tmp_path):
    from app.results.archive_safety import ArchiveSafetyError
    from app.results.import_run import ImportRejected, import_archive

    def add_unlisted(entries):
        entries["workspace/private.txt"] = b"private"

    unlisted = _rewrite_archive(exported_run["archive"], tmp_path / "unlisted.zip", add_unlisted)
    with pytest.raises(ImportRejected, match="unexpected"):
        await import_archive(unlisted)

    def add_traversal(entries):
        entries["artifacts/../../outside.txt"] = b"escape"

    traversal = _rewrite_archive(exported_run["archive"], tmp_path / "traversal.zip", add_traversal)
    with pytest.raises(ArchiveSafetyError):
        await import_archive(traversal)
    assert not (tmp_path / "outside.txt").exists()


@pytest.mark.asyncio
async def test_rename_failure_rolls_back_rows_and_staging(exported_run, monkeypatch):
    from app import config
    from app.db import engine as db_engine
    from app.db.models import Run
    from app.results import import_run

    async with db_engine.session_factory()() as session:
        before_count = (await session.execute(select(func.count()).select_from(Run))).scalar_one()
    runs_dir = config.get_settings().outputs_dir / "runs"
    before_dirs = {path.name for path in runs_dir.iterdir()}

    def fail_rename(_staging, _final):
        raise OSError("injected rename failure")

    monkeypatch.setattr(import_run, "_rename_staging", fail_rename)
    with pytest.raises(OSError, match="injected"):
        await import_run.import_archive(exported_run["archive"])

    async with db_engine.session_factory()() as session:
        after_count = (await session.execute(select(func.count()).select_from(Run))).scalar_one()
    assert after_count == before_count
    assert {path.name for path in runs_dir.iterdir()} == before_dirs
    assert not list(runs_dir.glob(".importing-*"))


def test_abandoned_import_cleanup_never_follows_symlinks(tmp_env):
    from app import config
    from app.results.import_run import cleanup_abandoned_imports

    runs_dir = config.get_settings().outputs_dir / "runs"
    runs_dir.mkdir(parents=True)
    abandoned = runs_dir / ".importing-directory"
    abandoned.mkdir()
    (abandoned / "partial").write_text("partial", encoding="utf-8")
    outside = tmp_env / "outside"
    outside.mkdir()
    (outside / "keep").write_text("keep", encoding="utf-8")
    link = runs_dir / ".importing-link"
    os.symlink(outside, link)
    keep = runs_dir / "completed-run"
    keep.mkdir()

    cleanup_abandoned_imports()

    assert not abandoned.exists()
    assert not link.exists()
    assert (outside / "keep").read_text(encoding="utf-8") == "keep"
    assert keep.is_dir()


@pytest.mark.asyncio
async def test_startup_reconciles_promoted_import_markers(tmp_env):
    from app import config
    from app.results.import_run import cleanup_uncommitted_imports

    await seed_catalog()
    committed_id = await make_run(task_keys=["fixture-0001"])
    runs_dir = config.get_settings().outputs_dir / "runs"
    committed = runs_dir / committed_id
    committed.mkdir(parents=True)
    (committed / ".importing").write_text(committed_id, encoding="utf-8")

    orphan_id = "f" * 32
    orphan = runs_dir / orphan_id
    orphan.mkdir()
    (orphan / ".importing").write_text(orphan_id, encoding="utf-8")
    (orphan / "partial").write_text("partial", encoding="utf-8")

    await cleanup_uncommitted_imports()

    assert committed.is_dir()
    assert not (committed / ".importing").exists()
    assert not orphan.exists()


@pytest.mark.asyncio
async def test_primary_session_without_artifacts_still_gets_a_fresh_row(exported_run, tmp_path):
    from app.db import engine as db_engine
    from app.db.models import AgentSession, RunTask
    from app.results.import_run import import_archive

    def remove_session_artifacts(entries):
        manifest = json.loads(entries["manifest.json"])
        session_paths = {
            item["path"] for item in manifest["artifacts"] if "/sessions/" in item["path"]
        }
        manifest["artifacts"] = [
            item for item in manifest["artifacts"] if item["path"] not in session_paths
        ]
        entries["manifest.json"] = json.dumps(manifest).encode()
        for path in session_paths:
            entries.pop(path)

    archive = _rewrite_archive(
        exported_run["archive"], tmp_path / "no-session-files.zip", remove_session_artifacts,
    )
    run_id = await import_archive(archive)
    async with db_engine.session_factory()() as session:
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == run_id)
        )).scalar_one()
        agent_session = (await session.execute(
            select(AgentSession).where(AgentSession.run_task_id == run_task.id)
        )).scalar_one()
    assert agent_session.id != exported_run["session_id"]
    assert agent_session.status == "ended"


@pytest.mark.asyncio
async def test_upload_is_rejected_at_streaming_limit(tmp_env, monkeypatch):
    import httpx

    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    from app import config

    config.get_settings.cache_clear()
    settings = config.get_settings()
    settings.import_limits = replace(settings.import_limits, max_upload_bytes=32, chunk_bytes=8)
    from app.main import app

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/runs/import",
                files={"file": ("large.zip", b"x" * 64, "application/zip")},
            )
    assert response.status_code == 413
    runs_dir = settings.outputs_dir / "runs"
    assert not list(runs_dir.glob(".importing-*"))