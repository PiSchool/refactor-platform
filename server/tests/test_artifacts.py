from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import select

from tests.helpers import FIXTURES, make_run, seed_catalog


_OPENROUTER_SECRET = "sk-or-v1-step8-canary-abcdefghijklmnopqrstuvwxyz"
# Invented credentials, kept in the shape the redactor matches by pattern rather
# than by value. They are assembled here because a literal of that shape is
# rejected by secret scanning on a public repository even when the value is not
# real, and weakening the shape would stop exercising the rule under test.
_AWS_ACCESS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"
_AWS_SECRET_KEY = "0123456789abcdef" + "ghijklmnopqrstuvwxyzABCD"


@pytest.fixture()
async def evidence(tmp_env, monkeypatch):
    monkeypatch.setenv("RP_PLUGINS_DIR", str(FIXTURES))
    monkeypatch.setenv("OPENROUTER_API_KEY", _OPENROUTER_SECRET)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", _AWS_ACCESS_KEY)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", _AWS_SECRET_KEY)
    monkeypatch.setenv("RP_EVIDENCE_VIEW_MAX_BYTES", "1024")
    monkeypatch.setenv("RP_EVIDENCE_DOWNLOAD_MAX_BYTES", "2048")

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
        run.config = {
            "sourcePath": str(tmp_env / "private-source"),
            "nested": {"apiToken": _OPENROUTER_SECRET},
        }
        rt.status = "passed"
        rt.started_at = rt.finished_at = utcnow()

        root = config.get_settings().outputs_dir / "runs" / run_id / "tasks" / rt.id
        session_id = "session-one"
        session_root = root / "agent-session" / session_id
        events = session_root / "home" / ".copilot" / "session-state" / "owned" / "events.jsonl"
        for directory in (
            root / "retrieval",
            root / "eval",
            root / "eval" / "self-checks" / "attempt-0001" / "logs",
            events.parent,
            root / "workspace",
        ):
            directory.mkdir(parents=True, exist_ok=True)

        (root / "prompt.md").write_text(
            f"Use this credential only as a canary: {_OPENROUTER_SECRET}\n",
            encoding="utf-8",
        )
        (root / "response.md").write_text(
            f"Authorization: Bearer {_OPENROUTER_SECRET}\n",
            encoding="utf-8",
        )
        (root / "diff.patch").write_text("diff --git a/a.py b/a.py\n", encoding="utf-8")
        (root / "workspace_meta.json").write_text(json.dumps({
            "baseline": "abc123",
            "workspacePath": str(root / "workspace"),
            "credential": _AWS_SECRET_KEY,
        }), encoding="utf-8")
        (root / "retrieval" / "context.md").write_text("Relevant code\n", encoding="utf-8")
        (root / "retrieval" / "queries.json").write_text(
            json.dumps(["rename symbol"]), encoding="utf-8",
        )
        (root / "retrieval" / "hits.json").write_text(
            json.dumps([{"path": "src/a.py", "score": 1.0}]), encoding="utf-8",
        )
        (root / "retrieval" / "provenance.json").write_text(json.dumps({
            "headers": {"Authorization": f"Bearer {_OPENROUTER_SECRET}"},
            "accessKey": _AWS_ACCESS_KEY,
        }), encoding="utf-8")
        (root / "retrieval" / "invocations.jsonl").write_text(
            json.dumps({"type": "search", "cookie": "session=private"}) + "\n",
            encoding="utf-8",
        )
        (root / "eval" / "python_tests.log").write_text(
            f"AWS_SECRET_ACCESS_KEY={_AWS_SECRET_KEY}\n5 passed\n", encoding="utf-8",
        )
        (root / "eval" / "self-checks" / "attempt-0001" / "result.json").write_text(
            json.dumps({"attempt": 1, "status": "passed", "token": _OPENROUTER_SECRET}),
            encoding="utf-8",
        )
        (root / "eval" / "self-checks" / "attempt-0001" / "logs" / "pytest.log").write_text(
            "self-check passed\n", encoding="utf-8",
        )
        (root / "eval" / "self-checks" / "limit-reached.json").write_text(
            json.dumps({"status": "attempt_limit", "maxAttempts": 1}), encoding="utf-8",
        )
        (session_root / "terminal.log").write_text(
            f"running from {root / 'workspace'}\nBearer {_OPENROUTER_SECRET}\n",
            encoding="utf-8",
        )
        (session_root / "transcript.txt").write_text("complete transcript\n", encoding="utf-8")
        events.write_text(json.dumps({
            "type": "session.start",
            "data": {"authorization": f"Bearer {_OPENROUTER_SECRET}"},
        }) + "\n", encoding="utf-8")

        # None of these private or non-catalogued files may enter an export.
        (root / "workspace" / "private.txt").write_text(_OPENROUTER_SECRET, encoding="utf-8")
        (session_root / "home" / ".copilot" / "config.json").write_text(
            _OPENROUTER_SECRET, encoding="utf-8",
        )
        (session_root / "mcp-config.json").write_text("internal topology", encoding="utf-8")
        executable = root / "run-me.sh"
        executable.write_text("#!/bin/sh\n", encoding="utf-8")
        executable.chmod(0o755)

        session.add(AgentSession(
            id=session_id,
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
            metrics={"setupCompliance": "conformant"},
            details={
                "retrieval": {
                    "provenancePath": str(root / "retrieval" / "provenance.json"),
                    "invocationsPath": str(root / "retrieval" / "invocations.jsonl"),
                },
                "authorization": f"Bearer {_OPENROUTER_SECRET}",
            },
            prompt_path=str(root / "prompt.md"),
            response_path=str(root / "response.md"),
            diff_path=str(root / "diff.patch"),
            terminal_path=str(session_root / "terminal.log"),
            events_path=str(events),
            eval_dir=str(root / "eval"),
        ))
        await session.commit()
        task_id = rt.id

    from app.api import wire_routes
    from app.main import create_app

    app = create_app()
    wire_routes(app)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield SimpleNamespace(
            client=client,
            run_id=run_id,
            task_id=task_id,
            session_id=session_id,
            root=root,
        )


def _task_url(case, key: str) -> str:
    return f"/api/runs/{case.run_id}/tasks/{case.task_id}/artifacts/{key}"


def _session_url(case, key: str) -> str:
    return (
        f"/api/runs/{case.run_id}/tasks/{case.task_id}/sessions/"
        f"{case.session_id}/artifacts/{key}"
    )


@pytest.mark.asyncio
async def test_run_repository_and_log_json_are_path_free(evidence):
    detail = await evidence.client.get(f"/api/runs/{evidence.run_id}")
    assert detail.status_code == 200
    body = detail.text
    assert str(evidence.root) not in body
    assert str(evidence.root.parents[4]) not in body
    assert "workspacePath" not in body
    assert "provenancePath" not in body
    assert "invocationsPath" not in body
    task = detail.json()["tasks"][0]
    assert {ref["key"] for ref in task["artifacts"]} >= {
        "prompt", "response", "diff", "workspace-meta", "retrieval-context",
    }
    assert {ref["key"] for ref in task["session"]["artifacts"]} == {
        "terminal", "transcript", "events",
    }

    repo = await evidence.client.get(
        f"/api/runs/{evidence.run_id}/tasks/{evidence.task_id}/repo"
    )
    assert repo.status_code == 200
    assert "workspacePath" not in repo.json()
    assert str(evidence.root) not in repo.text

    logs = await evidence.client.get(
        f"/api/runs/{evidence.run_id}/tasks/{evidence.task_id}/logs"
    )
    assert logs.status_code == 200
    assert str(evidence.root) not in logs.text
    assert all("path" not in row for row in logs.json()["logs"])


@pytest.mark.asyncio
async def test_artifact_lists_cover_every_evidence_family_and_media_type(evidence):
    response = await evidence.client.get(
        f"/api/runs/{evidence.run_id}/tasks/{evidence.task_id}/artifacts"
    )
    assert response.status_code == 200
    refs = {ref["key"]: ref for ref in response.json()["artifacts"]}
    expected = {
        "prompt", "response", "diff", "workspace-meta",
        "retrieval-context", "retrieval-queries", "retrieval-hits",
        "retrieval-provenance", "retrieval-invocations",
        "eval-log:python_tests", "self-check:0001:result",
        "self-check:0001:log:pytest", "self-check-limit",
    }
    assert expected <= refs.keys()
    assert all(refs[key]["available"] for key in expected)
    assert refs["prompt"]["mediaType"] == "text/markdown"
    assert refs["diff"]["mediaType"] == "text/x-diff"
    assert refs["workspace-meta"]["mediaType"] == "application/json"
    assert refs["retrieval-invocations"]["mediaType"] == "application/x-ndjson"
    assert refs["eval-log:python_tests"]["mediaType"] == "text/plain"
    for ref in refs.values():
        assert set(ref) == {
            "key", "available", "mediaType", "sizeBytes", "viewUrl", "downloadUrl",
        }
        assert str(evidence.root) not in json.dumps(ref)
        assert ref["viewUrl"].startswith("/api/runs/")
        assert ref["downloadUrl"].endswith("?download=1")

    sessions = await evidence.client.get(
        f"/api/runs/{evidence.run_id}/tasks/{evidence.task_id}/sessions/"
        f"{evidence.session_id}/artifacts"
    )
    assert sessions.status_code == 200
    assert {ref["key"] for ref in sessions.json()["artifacts"]} == {
        "terminal", "transcript", "events",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("key", "media"),
    [
        ("prompt", "text/markdown"),
        ("workspace-meta", "application/json"),
        ("retrieval-invocations", "application/x-ndjson"),
        ("eval-log:python_tests", "text/plain"),
        ("self-check:0001:result", "application/json"),
        ("self-check:0001:log:pytest", "text/plain"),
        ("self-check-limit", "application/json"),
    ],
)
async def test_task_evidence_is_sanitized_without_modifying_source(evidence, key, media):
    response = await evidence.client.get(_task_url(evidence, key))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(media)
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "private, no-store"
    assert _OPENROUTER_SECRET not in response.text
    assert _AWS_ACCESS_KEY not in response.text
    assert _AWS_SECRET_KEY not in response.text

    # Redaction is response-only: authoritative evidence stays untouched.
    assert _OPENROUTER_SECRET in (evidence.root / "prompt.md").read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ["terminal", "transcript", "events"])
async def test_session_evidence_is_owned_and_sanitized(evidence, key):
    response = await evidence.client.get(_session_url(evidence, key))
    assert response.status_code == 200
    assert _OPENROUTER_SECRET not in response.text
    assert str(evidence.root) not in response.text
    assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.asyncio
async def test_terminal_websocket_reader_matches_http_evidence(evidence):
    from app.db import engine as db_engine
    from app.db.models import AgentSession
    from app.realtime.ws_terminal import _redacted_reader

    response = await evidence.client.get(_session_url(evidence, "terminal"))
    async with db_engine.session_factory()() as session:
        row = await session.get(AgentSession, evidence.session_id)
    terminal_path = Path(row.terminal_path)
    websocket_bytes = _redacted_reader(terminal_path.parent)(
        terminal_path, 0, None
    )

    assert websocket_bytes == response.content
    assert _OPENROUTER_SECRET.encode() not in websocket_bytes
    assert str(evidence.root).encode() not in websocket_bytes


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "suffix",
    [
        "unknown",
        "eval-log:..",
        "eval-log:%2Fetc%2Fpasswd",
        "eval-log:%5Cetc%5Cpasswd",
        "self-check:1:result",
        "self-check:0001:log:..",
    ],
)
async def test_unknown_malformed_and_encoded_artifact_keys_fail_closed(evidence, suffix):
    response = await evidence.client.get(_task_url(evidence, suffix))
    assert response.status_code in {400, 404}


@pytest.mark.asyncio
async def test_cross_run_task_and_session_ownership_returns_404(evidence):
    other_run = await make_run(task_keys=["fixture-0001"])
    task_mismatch = await evidence.client.get(
        f"/api/runs/{other_run}/tasks/{evidence.task_id}/artifacts/prompt"
    )
    session_mismatch = await evidence.client.get(
        f"/api/runs/{other_run}/tasks/{evidence.task_id}/sessions/"
        f"{evidence.session_id}/artifacts/terminal"
    )
    assert task_mismatch.status_code == 404
    assert session_mismatch.status_code == 404


@pytest.mark.asyncio
async def test_symlink_non_regular_and_oversized_artifacts_fail_closed(evidence, tmp_path):
    outside = tmp_path / "outside.log"
    outside.write_text(_OPENROUTER_SECRET, encoding="utf-8")
    (evidence.root / "eval" / "escape.log").symlink_to(outside)
    fifo = evidence.root / "eval" / "pipe.log"
    os.mkfifo(fifo)
    (evidence.root / "eval" / "large.log").write_text("x" * 1500, encoding="utf-8")

    for key in ("eval-log:escape", "eval-log:pipe"):
        response = await evidence.client.get(_task_url(evidence, key))
        assert response.status_code == 404

    too_large = await evidence.client.get(_task_url(evidence, "eval-log:large"))
    assert too_large.status_code == 413
    downloadable = await evidence.client.get(_task_url(evidence, "eval-log:large") + "?download=1")
    assert downloadable.status_code == 200


def test_streaming_redaction_covers_credentials_split_between_chunks(tmp_path):
    from app.results.redaction import Redactor

    path = tmp_path / "split.log"
    path.write_text(
        f"before {_OPENROUTER_SECRET} middle Bearer {_AWS_SECRET_KEY} after",
        encoding="utf-8",
    )
    redactor = Redactor(secret_values=[_OPENROUTER_SECRET, _AWS_SECRET_KEY])
    output = b"".join(redactor.iter_text(path, chunk_size=7)).decode("utf-8")
    assert _OPENROUTER_SECRET not in output
    assert _AWS_SECRET_KEY not in output
    assert "[REDACTED]" in output


def test_incremental_terminal_redaction_matches_final_evidence(tmp_path):
    from app.results.redaction import IncrementalTextRedactor, Redactor

    path = tmp_path / "terminal.log"
    chunks = [
        b"before sk-or-secr",
        b"et0123456789 after\nprivate ",
        str(tmp_path).encode("utf-8")[:5],
        str(tmp_path).encode("utf-8")[5:] + b"\nlast line",
    ]
    path.write_bytes(b"".join(chunks))
    redactor = Redactor(
        secret_values=[_OPENROUTER_SECRET],
        private_paths=[tmp_path],
    )
    incremental = IncrementalTextRedactor(redactor)
    streamed = b"".join(
        [*(incremental.feed(chunk) for chunk in chunks), incremental.finalize()]
    )
    final = b"".join(redactor.iter_text(path, chunk_size=7))

    assert streamed == final
    assert b"sk-or-secret0123456789" not in streamed
    assert str(tmp_path).encode("utf-8") not in streamed


@pytest.mark.asyncio
async def test_export_uses_only_catalogued_sanitized_evidence(evidence):
    response = await evidence.client.get(f"/api/runs/{evidence.run_id}/export")
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        summary = archive.read("summary.json").decode("utf-8")
        assert str(evidence.root) not in summary
        assert "workspacePath" not in summary
        assert "provenancePath" not in summary
        assert "invocationsPath" not in summary
        assert _OPENROUTER_SECRET not in summary
        assert not any("workspace/" in name for name in names)
        assert not any(".copilot" in name for name in names)
        assert not any("mcp-config" in name for name in names)
        assert not any(name.endswith("run-me.sh") for name in names)

        # Archive folder names are export-local ids (task-0000/session-0000),
        # not the source run's live database identifiers.
        prompt_name = "artifacts/tasks/task-0000/prompt.md"
        events_name = "artifacts/tasks/task-0000/sessions/session-0000/events.jsonl"
        assert prompt_name in names
        assert events_name in names
        assert evidence.task_id not in summary
        assert evidence.session_id not in summary
        for name in names - {"results.csv"}:
            content = archive.read(name)
            assert _OPENROUTER_SECRET.encode() not in content
            assert _AWS_ACCESS_KEY.encode() not in content
            assert _AWS_SECRET_KEY.encode() not in content

        http_prompt = await evidence.client.get(_task_url(evidence, "prompt"))
        assert archive.read(prompt_name) == http_prompt.content
