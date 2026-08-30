"""Contracts every shipped agent adapter has to keep.

These assertions come from defects that reached a run: an adapter that named its
vendor to the CLI and let it bill a subscription instead of the run's provider,
an adapter whose translated stream collapsed a whole session into one step, and
an agent paired with an endpoint that cannot serve the request format it sends,
which surfaced inside the agent as a bare `404`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.catalog.loader import discover
from app.config import ProviderConfig
from app.execution import wire

PLUGINS = Path(__file__).resolve().parents[2] / "plugins"
#: adapters that translate a JSON stream through a wrapper of their own
STREAMED = ("claude", "opencode", "junie", "codex")


def agents() -> dict:
    found = discover(PLUGINS).agents
    return found if isinstance(found, dict) else {a.manifest.key: a for a in found}


@pytest.fixture(scope="module")
def shipped() -> dict:
    return agents()


def test_every_shipped_agent_declares_the_protocol_it_speaks(shipped):
    """An undeclared protocol defaults to chat completions, which is wrong for
    two of the shipped CLIs and would send them at an endpoint they cannot use."""
    expected = {
        "copilot": "chat_completions",
        "aider": "chat_completions",
        "opencode": "chat_completions",
        "junie": "chat_completions",
        "codex": "responses",
        "claude": "anthropic_messages",
    }
    assert {key: wire.required_protocol(loaded.impl) for key, loaded in shipped.items()} == expected


def test_a_provider_that_cannot_serve_an_agent_refuses_it_by_name(shipped):
    chat_only = ProviderConfig(
        key="plain", name="Plain endpoint", base_url="http://endpoint/v1",
        api_key_env="PLAIN_API_KEY", protocols=["chat_completions"],
    )
    refused = {
        key for key, loaded in shipped.items()
        if wire.refusal(loaded.manifest.name, loaded.impl, chat_only)
    }
    assert refused == {"codex", "claude"}

    reason = wire.refusal("Claude Code", shipped["claude"].impl, chat_only)
    assert "Anthropic Messages API" in reason and "Plain endpoint" in reason

    everything = ProviderConfig(
        key="full", name="Full endpoint", base_url="http://endpoint/v1",
        api_key_env="FULL_API_KEY",
        protocols=["chat_completions", "responses", "anthropic_messages"],
    )
    assert not any(
        wire.refusal(loaded.manifest.name, loaded.impl, everything)
        for loaded in shipped.values()
    )


def test_the_anthropic_root_drops_the_version_segment():
    """Claude Code appends `/v1/messages`, so it must be given the endpoint root.

    Passing the chat-completions URL produced `/api/v1/v1/messages` and a 404
    that read as though the model did not exist.
    """
    declared = ProviderConfig(
        key="openrouter", base_url="https://openrouter.ai/api/v1",
        anthropic_base_url="https://openrouter.ai/api",
    )
    derived = ProviderConfig(key="other", base_url="https://gateway.example/v1")
    assert declared.resolved_anthropic_base_url() == "https://openrouter.ai/api"
    assert derived.resolved_anthropic_base_url() == "https://gateway.example"


def test_no_adapter_lets_its_cli_fall_back_to_a_vendor_subscription(shipped):
    """Each CLI has a variable that would authenticate against its own vendor.

    Left set, a run reports the provider it declared while the request is billed
    somewhere else, and the recorded provenance is a lie.
    """
    cleared = {
        "claude": ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"),
        "copilot": ("COPILOT_GITHUB_TOKEN",),
        "junie": ("JUNIE_API_KEY",),
    }
    for key, variables in cleared.items():
        source = (PLUGINS / "agents" / key / "plugin.py").read_text(encoding="utf-8")
        for variable in variables:
            assert f'env["{variable}"] = ""' in source, f"{key} leaves {variable} set"


def _session(tmp_path: Path, model: str = "openrouter/free"):
    from app.catalog.sdk import SessionCtx, TaskDef, WorkspaceSpec

    workspace = tmp_path / "workspace"
    config_dir = tmp_path / "config"
    for path in (workspace, config_dir):
        path.mkdir(parents=True, exist_ok=True)
    task = TaskDef(
        task_key="t1", title="t1", language="python", instructions="rename it",
        workspace=WorkspaceSpec(type="git", source="https://example/repo", ref="c0ffee"),
    )
    return SessionCtx(
        run_id="r1", run_task_id="rt1", session_id="s1", task=task,
        workspace=workspace, artifacts_dir=tmp_path / "artifacts",
        prompt_path=tmp_path / "prompt.md", config_dir=config_dir, model=model,
        setup=None,
        requested_env={
            "RP_PROVIDER": "openrouter",
            "RP_PROVIDER_BASE_URL": "https://openrouter.ai/api/v1",
            "RP_PROVIDER_ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
            "RP_PROVIDER_API_KEY": "test-key",
        },
    )


def test_claude_is_pointed_at_the_declared_endpoint_and_keeps_its_home_private(tmp_path, shipped):
    session = _session(tmp_path)
    plugin = shipped["claude"].impl
    plugin.prepare(session)
    spec = plugin.command(session)
    env = spec.env
    assert env["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"
    assert env["ANTHROPIC_AUTH_TOKEN"] == "test-key"
    assert env["CLAUDE_CONFIG_DIR"].startswith(str(session.config_dir))
    assert "--output-format" in spec.argv and "stream-json" in spec.argv


def test_opencode_declares_the_resolved_endpoint_as_its_own_provider(tmp_path, shipped):
    session = _session(tmp_path)
    plugin = shipped["opencode"].impl
    plugin.prepare(session)
    config = json.loads((session.config_dir / "opencode.json").read_text(encoding="utf-8"))
    declared = config["provider"]["platform"]
    assert declared["options"]["baseURL"] == "https://openrouter.ai/api/v1"
    assert declared["options"]["apiKey"] == "test-key"
    assert "openrouter/free" in declared["models"]
    spec = plugin.command(session)
    assert "platform/openrouter/free" in spec.argv
    assert "--auto" in spec.argv, "a batch run has no operator to approve a tool"


def test_junie_reads_its_key_from_the_environment_rather_than_from_disk(tmp_path, shipped):
    """A profile file is world-readable inside the container and ends up in
    evidence bundles; Junie expands `${VAR}`, so the key stays out of it."""
    session = _session(tmp_path)
    plugin = shipped["junie"].impl
    plugin.prepare(session)
    home = session.config_dir / ".junie"
    profile = json.loads((home / "models" / "platform.json").read_text(encoding="utf-8"))
    assert profile["apiKey"] == "${RP_PROVIDER_API_KEY}"
    assert "test-key" not in (home / "models" / "platform.json").read_text(encoding="utf-8")
    assert profile["baseUrl"] == "https://openrouter.ai/api/v1/chat/completions"
    assert profile["apiType"] == "OpenAICompletion"
    config = json.loads((home / "config.json").read_text(encoding="utf-8"))
    assert config["brave"] is True, "no operator is present to approve a tool"
    assert config["model"] == "custom:platform"
    assert plugin.command(session).env["JUNIE_HOME"] == str(home)


def test_a_missing_base_url_is_named_rather_than_producing_a_broken_launch(tmp_path, shipped):
    for key in ("claude", "opencode", "junie"):
        session = _session(tmp_path / key)
        session.requested_env = {"RP_PROVIDER": "openrouter", "RP_PROVIDER_API_KEY": "k"}
        with pytest.raises(RuntimeError, match="provider"):
            shipped[key].impl.prepare(session)


@pytest.mark.parametrize("key", STREAMED)
def test_a_translated_stream_produces_bounded_turns(key, tmp_path, shipped):
    """One unbounded step is unreadable, which is what the Agent tab showed
    before each adapter delimited its own turns."""
    module = _events_module(key)
    translator = module.Translator("openrouter/free")
    produced = [translator.start(), translator.prompt("do the thing")]
    for line in _SAMPLE[key]:
        produced.extend(translator.feed(json.dumps(line)))
    produced.extend(translator.shutdown("completed"))

    kinds = [event["type"] for event in produced]
    assert kinds.count("assistant.turn_start") >= 2, kinds
    assert kinds.count("assistant.turn_start") == kinds.count("assistant.turn_end")
    assert "tool.execution_start" in kinds and "tool.execution_complete" in kinds

    path = tmp_path / f"{key}.jsonl"
    path.write_text("".join(json.dumps(event) + "\n" for event in produced), encoding="utf-8")
    parsed = module.parse(path, tmp_path / "absent.log", "openrouter/free")
    assert parsed["tokens_input"] > 0 and parsed["tokens_output"] > 0
    assert "second answer" in parsed["response_text"]
    assert parsed["readable_transcript"]


@pytest.mark.parametrize("key", STREAMED)
def test_a_translated_session_records_the_version_of_the_tool_that_ran(key):
    """The run view labels a session with the tool and its version. It used to
    read a Copilot-specific field, so every other tool was shown as `v?`; each
    adapter now reports the version its own command answered with."""
    module = _events_module(key)
    assert callable(getattr(module, "installed_version", None)), \
        f"{key} cannot read the version of the command it runs"
    start = module.Translator("openrouter/free", "1.2.3").start()
    assert start["data"]["version"] == "1.2.3"


def test_junie_runs_the_task_without_asking_for_a_terminal(tmp_path, shipped):
    """`--prompt` opens the interactive interface with the text submitted; with
    no terminal to answer, a run ended in seconds having changed nothing."""
    session = _session(tmp_path)
    plugin = shipped["junie"].impl
    plugin.prepare(session)
    argv = plugin.command(session).argv
    tool = argv[argv.index("--") + 1:]
    assert tool[0] == "junie"
    assert "--prompt" not in tool
    assert tool[tool.index("--output-format") + 1] == "json-stream"
    assert "--session-id" not in tool, "nothing to resume on a first attempt"

    recorded = session.config_dir / "junie-session-id"
    recorded.write_text("session-260728-005254-1mns", encoding="utf-8")
    resumed = plugin.resume_command(session, session.prompt_path).argv
    assert resumed[resumed.index("--session-id") + 1] == "session-260728-005254-1mns"


def _events_module(key: str):
    import importlib.util

    path = PLUGINS / "agents" / key / "events.py"
    spec = importlib.util.spec_from_file_location(f"_events_{key}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: One recorded shape per CLI: two model steps, a tool call and its result, and
#: usage. Taken from real streams captured against the provider.
_SAMPLE = {
    "claude": [
        {"type": "system", "subtype": "init", "model": "openrouter/free"},
        {"type": "assistant", "message": {"usage": {"output_tokens": 3}, "content": [
            {"type": "text", "text": "first answer"}]}},
        {"type": "assistant", "message": {"usage": {"output_tokens": 5}, "content": [
            {"type": "tool_use", "id": "c1", "name": "Edit", "input": {"file_path": "a.py"}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "c1", "content": "edited"}]}},
        {"type": "assistant", "message": {"usage": {"output_tokens": 7}, "content": [
            {"type": "text", "text": "second answer"}]}},
        {"type": "result", "is_error": False, "num_turns": 2, "result": "second answer",
         "usage": {"input_tokens": 900, "output_tokens": 12}},
    ],
    "opencode": [
        {"type": "step_start", "part": {"type": "step-start"}},
        {"type": "tool_use", "part": {"type": "tool", "tool": "edit", "callID": "c1", "state": {
            "status": "completed", "input": {"filePath": "a.py"}, "output": "Edit applied"}}},
        {"type": "step_finish", "part": {"type": "step-finish", "reason": "tool-calls",
                                        "tokens": {"input": 500, "output": 5}}},
        {"type": "step_start", "part": {"type": "step-start"}},
        {"type": "text", "part": {"type": "text", "text": "second answer"}},
        {"type": "step_finish", "part": {"type": "step-finish", "reason": "stop",
                                         "tokens": {"input": 400, "output": 7}}},
    ],
    # Recorded from `junie --task … --output-format json-stream`: a step is one
    # unit of work, and the closing frame carries the per-model token records.
    "junie": [
        {"type": "session", "sessionId": "session-260728-005254-1mns"},
        {"type": "step", "name": "cat a.py", "details": "The contents were displayed.",
         "output": "def old_name(x): ..."},
        {"type": "step", "name": "Edited files", "details": "Updated a.py"},
        {"type": "step", "name": "TASK RESULT", "details": "first answer"},
        {"type": "result", "result": "second answer",
         "changes": [{"afterRelativePath": "a.py"}],
         "errorCode": [{"model": "openrouter/free", "calls": 4,
                        "inputTokens": 900, "outputTokens": 12}]},
    ],
    "codex": [
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "command_execution", "id": "c1",
                                            "command": "ls", "exit_code": 0,
                                            "aggregated_output": "a.py"}},
        {"type": "turn.completed", "usage": {"input_tokens": 500, "output_tokens": 5}},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "id": "m1",
                                            "text": "second answer"}},
        {"type": "turn.completed", "usage": {"input_tokens": 400, "output_tokens": 7}},
    ],
}


# ── Junie retries a failed model request ─────────────────────────────────────
#
# Junie ends the whole task when one model request fails, where the other CLIs
# retry internally: a single dropped request on a free router cost a task that
# had already edited a file. The wrapper resumes the session Junie recorded.

_FAKE_JUNIE = '''#!/usr/bin/env python3
import json, os, sys

argv = sys.argv[1:]
if "--version" in argv:
    print("Junie version: 26.7.20 (2383.10)")
    raise SystemExit(0)

log = os.environ["FAKE_JUNIE_LOG"]
with open(log, "a", encoding="utf-8") as sink:
    sink.write(json.dumps(argv) + "\\n")

print(json.dumps({"type": "session", "sessionId": "abc123"}), flush=True)
resumed = "--session-id" in argv
if not resumed and os.environ.get("FAKE_JUNIE_FAIL", "1") == "1":
    print(json.dumps({"type": "error",
                      "error": os.environ.get("FAKE_JUNIE_ERROR",
                                              "Failed to build 'issue.md.junie_standalone'")}),
          flush=True)
    raise SystemExit(1)
print(json.dumps({"type": "step", "name": "Edited files", "details": "Updated a.py"}), flush=True)
print(json.dumps({"type": "result", "result": "done",
                  "changes": [{"afterRelativePath": "a.py"}]}), flush=True)
raise SystemExit(0)
'''


def _run_junie_wrapper(tmp_path: Path, *, error: str, retries: int = 2) -> tuple[int, list[list[str]], Path, Path]:
    """Drive the real wrapper against a CLI that fails once, then succeeds."""
    import os
    import subprocess
    import sys

    fake = tmp_path / "junie"
    fake.write_text(_FAKE_JUNIE, encoding="utf-8")
    fake.chmod(0o755)
    calls = tmp_path / "calls.jsonl"
    events = tmp_path / "events.jsonl"
    session_file = tmp_path / "session-id"
    prompt = tmp_path / "prompt.md"
    prompt.write_text("rename it\n", encoding="utf-8")
    terminal = tmp_path / "terminal.log"

    done = subprocess.run(
        [sys.executable, str(PLUGINS / "agents" / "junie" / "run.py"),
         "--events", str(events), "--prompt", str(prompt), "--model", "openrouter/free",
         "--junie-home", str(tmp_path / "home"), "--session-file", str(session_file),
         "--retries", str(retries), "--", str(fake), "--output-format", "json-stream"],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "FAKE_JUNIE_LOG": str(calls), "FAKE_JUNIE_ERROR": error},
    )
    terminal.write_text(done.stdout + done.stderr, encoding="utf-8")
    recorded = [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]
    return done.returncode, recorded, events, terminal


def test_junie_resumes_its_session_after_a_failed_model_request(tmp_path):
    code, calls, events, terminal = _run_junie_wrapper(
        tmp_path, error="Failed to build 'issue.md.junie_standalone'")

    assert code == 0, "the retry has to carry the task to a result"
    assert len(calls) == 2, calls
    assert "--session-id" not in calls[0]
    assert calls[1][calls[1].index("--session-id") + 1] == "abc123"

    recorded = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    notes = [row["data"]["content"] for row in recorded if row["type"] == "system.message"]
    assert any("retry 1 of 2" in note and "abc123" in note for note in notes), notes

    # A failure the retry got past is not the outcome, so the verdict must not
    # name a provider error on a session that finished.
    module = _events_module("junie")
    parsed = module.parse(events, terminal, "openrouter/free")
    assert "provider_error" not in parsed["flags"]
    assert parsed["response_text"] == "done"


def test_junie_does_not_retry_a_rejected_key(tmp_path):
    """Retrying an authentication failure spends the task's time budget on a
    request that cannot succeed."""
    code, calls, events, _ = _run_junie_wrapper(tmp_path, error="401 Unauthorized: invalid api key")

    assert code == 1
    assert len(calls) == 1, calls
    recorded = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    assert not any("retry" in json.dumps(row) for row in recorded)
