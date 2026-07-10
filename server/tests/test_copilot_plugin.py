from __future__ import annotations

import sys
from pathlib import Path

import pytest

EVENTS = Path(__file__).parent / "fixtures" / "events"
COPILOT = Path(__file__).resolve().parents[2] / "plugins" / "agents" / "copilot"


@pytest.fixture()
def parser():
    sys.path.insert(0, str(COPILOT))
    import events as ev
    return ev


@pytest.mark.parametrize("fixture", sorted(EVENTS.glob("*.jsonl")))
def test_parse_real_events(parser, fixture):
    info = parser.parse(fixture, None)
    assert info.tokens_input > 0, "should parse input tokens from session.shutdown"
    assert info.tokens_output > 0
    assert info.model, "should parse a model name"
    assert isinstance(info.readable_transcript, str)


def test_flags_from_terminal(parser, tmp_path):
    log = tmp_path / "terminal.log"
    log.write_text("... Please use /login to sign in to GitHub ...")
    flags = parser._scan_terminal(log)
    assert "auth_wall" in flags


def test_copilot_command_excludes_task_for_s1(tmp_env, tmp_path):
    from app.catalog.sdk import SessionCtx, SetupProfile, TaskDef, WorkspaceSpec
    from app.execution.setups import SETUPS

    sys.path.insert(0, str(COPILOT))
    import plugin as cp
    p = cp.Plugin()
    task = TaskDef("t", "t", "python", WorkspaceSpec("snapshot", "r"), "do", {})
    ctx = SessionCtx(run_id="r", run_task_id="rt", session_id="sid", task=task,
                     workspace=tmp_path, artifacts_dir=tmp_path, prompt_path=tmp_path / "p.md",
                     config_dir=tmp_path / "home", model="openrouter/free", setup=SETUPS["s1"],
                     requested_env={"OPENROUTER_API_KEY": "k", "OPENROUTER_BASE_URL": "https://x/v1"})
    (tmp_path / "p.md").write_text("hi")
    p.prepare(ctx)
    cmd = p.command(ctx)
    assert "--excluded-tools" in cmd.argv and "task" in cmd.argv
    assert cmd.env["COPILOT_PROVIDER_API_KEY"] == "k"
    assert cmd.env["COPILOT_GITHUB_TOKEN"] == ""
    # s3 enables sub-agents (no exclusion)
    ctx.setup = SETUPS["s3"]
    assert "--excluded-tools" not in p.command(ctx).argv


def _write_events(tmp_path, rows):
    import json
    p = tmp_path / "events.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_parse_extracts_cache_reasoning_context_and_compaction(tmp_path, parser):
    """Cost and context analysis need more than input/output totals."""
    rows = [
        {"type": "session.compaction_complete", "data": {"success": True}},
        {"type": "session.compaction_complete", "data": {"success": False}},   # not counted
        {"type": "session.error", "data": {"message": "400 maximum context length exceeded"}},
        {"type": "session.error", "data": {"message": "400 Provider returned error"}},  # not overflow
        {"type": "session.shutdown", "data": {
            "currentTokens": 45921,
            "modelMetrics": {"m/x": {"usage": {
                "inputTokens": 614426, "outputTokens": 15804,
                "cacheReadTokens": 377216, "reasoningTokens": 6769}}},
        }},
    ]
    info = parser.parse(_write_events(tmp_path, rows), None)
    assert info.tokens_input == 614426 and info.tokens_output == 15804
    assert info.tokens_cache_read == 377216
    assert info.tokens_reasoning == 6769
    assert info.context_tokens == 45921
    assert info.compaction_count == 1        # the failed compaction does not count
    assert info.context_overflow_count == 1  # only the context-limit error


def test_context_overflow_matcher(parser):
    ev = parser
    assert ev._is_context_overflow({"message": "This model's maximum context length is 8192 tokens"})
    assert ev._is_context_overflow({"message": "prompt is too long"})
    assert not ev._is_context_overflow({"message": "rate limited"})
    assert not ev._is_context_overflow({})
