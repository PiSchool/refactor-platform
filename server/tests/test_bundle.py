from __future__ import annotations

import hashlib
import json
import zipfile
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from tests.helpers import FIXTURES, make_run, seed_catalog


@pytest.fixture()
async def bundle_case(tmp_env, monkeypatch):
    """A minimal, fully-catalogued run: one task, one session, no secrets.

    Unlike `test_artifacts.py`'s `evidence` fixture, this exists purely to
    exercise the manifest/export-id contract, not redaction coverage.
    """
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))

    from app import config

    config.get_settings.cache_clear()
    await seed_catalog()
    run_id = await make_run(task_keys=["fixture-0001"])

    from app.db import engine as db_engine
    from app.db.models import AgentSession, Run, RunTask, TaskResult, utcnow

    async with db_engine.session_factory()() as session:
        run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one()
        rt = (await session.execute(
            select(RunTask).where(RunTask.run_id == run_id)
        )).scalar_one()
        run.status = "completed"
        run.started_at = run.finished_at = utcnow()
        rt.status = "passed"
        rt.started_at = rt.finished_at = utcnow()

        root = config.get_settings().outputs_dir / "runs" / run_id / "tasks" / rt.id
        live_session_id = "live-session-id"
        session_root = root / "agent-session" / live_session_id
        session_root.mkdir(parents=True, exist_ok=True)
        root.mkdir(parents=True, exist_ok=True)

        (root / "prompt.md").write_text("Refactor this function.\n", encoding="utf-8")
        (root / "response.md").write_text("Done.\n", encoding="utf-8")
        (root / "diff.patch").write_text("diff --git a/a.py b/a.py\n", encoding="utf-8")
        (root / "workspace_meta.json").write_text(
            json.dumps({"baseline": "abc123"}), encoding="utf-8",
        )
        (session_root / "terminal.log").write_text("session output\n", encoding="utf-8")
        (session_root / "transcript.txt").write_text("full transcript\n", encoding="utf-8")
        events = session_root / "events.jsonl"
        events.write_text(json.dumps({"type": "session.start"}) + "\n", encoding="utf-8")

        session.add(AgentSession(
            id=live_session_id,
            run_task_id=rt.id,
            status="ended",
            terminal_path=str(session_root / "terminal.log"),
            events_path=str(events),
            started_at=utcnow(),
            finished_at=utcnow(),
        ))
        session.add(TaskResult(
            run_task_id=rt.id,
            passed=True,
            reason="passed",
            model="stub-model",
            metrics={},
            details={},
            prompt_path=str(root / "prompt.md"),
            response_path=str(root / "response.md"),
            diff_path=str(root / "diff.patch"),
            terminal_path=str(session_root / "terminal.log"),
            events_path=str(events),
        ))
        await session.commit()
        task_id = rt.id

    return SimpleNamespace(run_id=run_id, task_id=task_id, live_session_id=live_session_id)


@pytest.mark.asyncio
async def test_manifest_present_with_expected_top_level_shape(bundle_case):
    from app.results.export import build_zip

    zip_path = await build_zip(bundle_case.run_id)
    with zipfile.ZipFile(zip_path) as archive:
        assert "manifest.json" in archive.namelist()
        manifest = json.loads(archive.read("manifest.json"))

    assert set(manifest) == {
        "format", "createdAt", "sourceRunId", "benchmark", "setup",
        "agentTool", "status", "taskCount", "artifacts",
    }
    assert manifest["format"] == "refactor-platform-run"
    assert manifest["sourceRunId"] == bundle_case.run_id
    assert manifest["status"] == "completed"
    assert manifest["taskCount"] == 1
    assert manifest["createdAt"]
    for ref_key in ("benchmark", "setup", "agentTool"):
        ref = manifest[ref_key]
        assert set(ref) == {"key", "name"}
        assert ref["key"] and ref["name"]


@pytest.mark.asyncio
async def test_manifest_artifact_inventory_matches_hashed_zip_bytes(bundle_case):
    from app.results.export import build_zip

    zip_path = await build_zip(bundle_case.run_id)
    with zipfile.ZipFile(zip_path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        names = set(archive.namelist())
        entries = manifest["artifacts"]
        assert entries, "expected at least one catalogued artifact"
        for entry in entries:
            assert set(entry) == {"path", "sizeBytes", "sha256", "mediaType"}
            assert entry["path"] in names
            content = archive.read(entry["path"])
            assert entry["sizeBytes"] == len(content)
            assert entry["sha256"] == hashlib.sha256(content).hexdigest()
        artifact_members = {n for n in names if n.startswith("artifacts/")}
        assert artifact_members == {entry["path"] for entry in entries}


@pytest.mark.asyncio
async def test_summary_and_artifact_paths_use_export_local_ids(bundle_case):
    from app.results.export import build_zip

    zip_path = await build_zip(bundle_case.run_id)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        summary = json.loads(archive.read("summary.json"))

    task_summary = summary["tasks"][0]
    export_task_id = task_summary["id"]
    dumped_summary = json.dumps(summary)
    assert export_task_id != bundle_case.task_id
    assert bundle_case.task_id not in dumped_summary

    session_summary = task_summary.get("session")
    assert session_summary is not None
    export_session_id = session_summary["id"]
    assert export_session_id != bundle_case.live_session_id
    assert bundle_case.live_session_id not in dumped_summary

    prompt_path = f"artifacts/tasks/{export_task_id}/prompt.md"
    events_path = f"artifacts/tasks/{export_task_id}/sessions/{export_session_id}/events.jsonl"
    assert prompt_path in names
    assert events_path in names


@pytest.mark.asyncio
async def test_results_csv_unchanged_alongside_manifest(bundle_case):
    from app.api.serializers import run_task_detail
    from app.db import engine as db_engine
    from app.db.models import RunTask
    from app.results.export import build_zip, results_csv

    zip_path = await build_zip(bundle_case.run_id)
    with zipfile.ZipFile(zip_path) as archive:
        csv_text = archive.read("results.csv").decode("utf-8")

    async with db_engine.session_factory()() as s:
        rt = (await s.execute(
            select(RunTask).where(RunTask.run_id == bundle_case.run_id)
        )).scalar_one()
        tasks = [await run_task_detail(rt, s)]
    assert csv_text == results_csv(tasks)


def test_run_manifest_model_serializes_expected_aliases():
    from app.results.bundle import ArtifactManifestEntry, PluginRef, build_manifest

    manifest = build_manifest(
        source_run_id="run-123",
        benchmark=PluginRef(key="bench", name="Bench"),
        setup=PluginRef(key="s1", name="Single agent"),
        agent_tool=PluginRef(key="stub", name="Stub"),
        status="completed",
        task_count=3,
        artifacts=[
            ArtifactManifestEntry(
                path="artifacts/tasks/task-0000/prompt.md",
                sizeBytes=12,
                sha256="a" * 64,
                mediaType="text/markdown",
            ),
        ],
    )
    dumped = manifest.model_dump(mode="json", by_alias=True)
    assert dumped["format"] == "refactor-platform-run"
    assert dumped["sourceRunId"] == "run-123"
    assert dumped["taskCount"] == 3
    assert dumped["agentTool"] == {"key": "stub", "name": "Stub"}
    assert dumped["artifacts"][0]["sizeBytes"] == 12


@pytest.mark.asyncio
async def test_export_response_removes_temporary_archive(monkeypatch, tmp_path):
    from app.api.runs import export_run
    from app.results import export as export_module

    export_dir = tmp_path / "rp-export-fixture"
    export_dir.mkdir()
    archive_path = export_dir / "run-fixture.zip"
    archive_path.write_bytes(b"zip bytes")

    async def fake_build_zip(_run_id):
        return archive_path

    monkeypatch.setattr(export_module, "build_zip", fake_build_zip)
    response = await export_run("fixture")
    assert response.background is not None
    await response.background()
    assert not export_dir.exists()
