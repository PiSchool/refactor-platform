from __future__ import annotations

import json
from pathlib import Path

import pytest

EVENTS = Path(__file__).parent / "fixtures" / "events"
COPILOT = Path(__file__).resolve().parents[2] / "plugins" / "agents" / "copilot"

# What the platform hands any adapter: which provider, where it is, and the key.
# No vendor variable appears here, and none should be needed.
PROVIDER_ENV = {
    "RP_PROVIDER": "acme",
    "RP_PROVIDER_BASE_URL": "https://llm.acme.test/v1",
    "RP_PROVIDER_API_KEY": "k",
}


@pytest.fixture()
def parser():
    from app.catalog.loader import import_plugin_module

    return import_plugin_module(COPILOT, "events")


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

    from app.catalog.loader import import_plugin_module
    cp = import_plugin_module(COPILOT, "plugin")
    p = cp.Plugin()
    task = TaskDef("t", "t", "python", WorkspaceSpec("snapshot", "r"), "do", {})
    ctx = SessionCtx(run_id="r", run_task_id="rt", session_id="sid", task=task,
                     workspace=tmp_path, artifacts_dir=tmp_path, prompt_path=tmp_path / "p.md",
                     config_dir=tmp_path / "home", model="openrouter/free", setup=SETUPS["s1"],
                     requested_env=PROVIDER_ENV)
    (tmp_path / "p.md").write_text("hi")
    p.prepare(ctx)
    cmd = p.command(ctx)
    assert "--excluded-tools" in cmd.argv and "task" in cmd.argv
    assert cmd.env["COPILOT_PROVIDER_API_KEY"] == "k"
    assert cmd.env["COPILOT_GITHUB_TOKEN"] == ""
    # s3 enables sub-agents (no exclusion)
    ctx.setup = SETUPS["s3"]
    assert "--excluded-tools" not in p.command(ctx).argv


def test_copilot_command_receives_generic_mcp_config(tmp_env, tmp_path):
    from app.catalog.sdk import SessionCtx, TaskDef, WorkspaceSpec
    from app.execution.setups import SETUPS

    from app.catalog.loader import import_plugin_module
    cp = import_plugin_module(COPILOT, "plugin")

    plugin = cp.Plugin()
    task = TaskDef("t", "t", "python", WorkspaceSpec("snapshot", "r"), "do", {})
    ctx = SessionCtx(
        run_id="r", run_task_id="rt", session_id="sid", task=task,
        workspace=tmp_path, artifacts_dir=tmp_path, prompt_path=tmp_path / "p.md",
        config_dir=tmp_path / "home", model="openrouter/free",
        setup=SETUPS["s2_rag_ast"], requested_env=PROVIDER_ENV,
        mcp_config={"mcpServers": {"codebase": {
            "command": "python", "args": ["-m", "server"],
        }}},
    )
    ctx.prompt_path.write_text("hi")

    plugin.prepare(ctx)
    cmd = plugin.command(ctx)

    assert "--additional-mcp-config" in cmd.argv
    config_arg = cmd.argv[cmd.argv.index("--additional-mcp-config") + 1]
    assert config_arg.startswith("@")
    assert json.loads(Path(config_arg[1:]).read_text()) == ctx.mcp_config
    assert plugin.capabilities["retrieval"] is True


def test_copilot_command_requires_provider_credentials(tmp_env, tmp_path):
    from app.catalog.sdk import SessionCtx, TaskDef, WorkspaceSpec
    from app.execution.setups import SETUPS

    from app.catalog.loader import import_plugin_module
    cp = import_plugin_module(COPILOT, "plugin")

    task = TaskDef("t", "t", "python", WorkspaceSpec("snapshot", "r"), "do", {})
    ctx = SessionCtx(
        run_id="r", run_task_id="rt", session_id="sid", task=task,
        workspace=tmp_path, artifacts_dir=tmp_path, prompt_path=tmp_path / "p.md",
        config_dir=tmp_path / "home", model="openrouter/free", setup=SETUPS["s1"],
        requested_env={"COPILOT_GITHUB_TOKEN": "must-not-be-used"},
    )
    ctx.prompt_path.write_text("hi")

    plugin = cp.Plugin()
    plugin.prepare(ctx)
    # the message names the provider the operator selected, not a vendor the
    # adapter happens to know about
    with pytest.raises(RuntimeError, match="no base URL configured for provider"):
        plugin.command(ctx)

    ctx.requested_env = {**PROVIDER_ENV, "RP_PROVIDER_API_KEY": ""}
    with pytest.raises(RuntimeError, match="no API key configured for provider 'acme'"):
        plugin.command(ctx)


def test_copilot_resume_command_keeps_session_and_model(tmp_env, tmp_path):
    from app.catalog.sdk import SessionCtx, TaskDef, WorkspaceSpec
    from app.execution.setups import SETUPS

    from app.catalog.loader import import_plugin_module
    cp = import_plugin_module(COPILOT, "plugin")

    task = TaskDef("t", "t", "python", WorkspaceSpec("snapshot", "r"), "do", {})
    prompt = tmp_path / "continue.md"
    prompt.write_text("run the required check")
    ctx = SessionCtx(
        run_id="r", run_task_id="rt", session_id="named-session", task=task,
        workspace=tmp_path, artifacts_dir=tmp_path, prompt_path=tmp_path / "p.md",
        config_dir=tmp_path / "home", model="openrouter/free", setup=SETUPS["s1_eval"],
        requested_env=PROVIDER_ENV,
    )

    cmd = cp.Plugin().resume_command(ctx, prompt)

    assert "--resume=named-session" in cmd.argv
    assert "--name" not in cmd.argv
    assert cmd.argv[cmd.argv.index("--model") + 1] == "openrouter/free"
    assert f"@{prompt}" in cmd.argv


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


def test_setup_fidelity_counters_from_real_tool_names(tmp_path):
    """`lsp`, `task` and `bash eval.sh` are the observable evidence that an
    S1-LSP / S3 / S1-eval run differed from a plain S1 run."""
    from app.catalog.loader import import_plugin_module
    ev = import_plugin_module(COPILOT, "events")

    log = tmp_path / "events.jsonl"
    log.write_text("\n".join([
        '{"type":"tool.execution_start","data":{"toolName":"lsp","arguments":{"operation":"hover"}}}',
        '{"type":"tool.execution_start","data":{"toolName":"lsp","arguments":{"operation":"documentSymbol"}}}',
        '{"type":"tool.execution_start","data":{"toolName":"task","arguments":{"agent":"analyst"}}}',
        '{"type":"tool.execution_start","data":{"toolName":"bash","arguments":{"command":"bash eval.sh"}}}',
        '{"type":"tool.execution_start","data":{"toolName":"view","arguments":{"file":"a.py"}}}',
    ]) + "\n")
    info = ev.parse(log, None, "m")
    assert info.lsp_actions == 2
    assert info.subagent_invocations == 1
    assert info.eval_tool_invocations == 1 and info.eval_iterations == 1


def test_setup_exercised_is_none_for_a_baseline_and_false_when_ignored():
    from app.catalog.sdk import SessionInfo, SetupProfile
    from app.execution.taskloop import _setup_exercised

    s1 = SetupProfile(key="s1", name="S1", description="")
    lsp = SetupProfile(key="s1_lsp", name="S1+LSP", description="", lsp=True)
    sub = SetupProfile(key="s3", name="S3", description="", subagents=True)

    assert _setup_exercised(s1, SessionInfo()) is None          # nothing to exercise
    assert _setup_exercised(lsp, SessionInfo()) is False        # server offered, never called
    assert _setup_exercised(lsp, SessionInfo(lsp_actions=1)) is True
    assert _setup_exercised(sub, SessionInfo()) is False
    assert _setup_exercised(sub, SessionInfo(subagent_invocations=2)) is True
