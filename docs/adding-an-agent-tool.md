# Adding an AI CLI tool

An agent tool is a directory under `plugins/agents/<key>/` with a `plugin.yaml`
and a `plugin.py` implementing `AgentPlugin`. The platform owns the process
lifecycle (PTY, timeout, kill, logging); your adapter only declares **how to
invoke** the tool and **how to interpret** its output.

## The request format a CLI sends

Agent CLIs do not agree on how to reach a model. Declare which format yours
sends by setting `wire` on the plugin class:

| `wire` | Sent to | CLIs that use it |
|---|---|---|
| `chat_completions` (default) | `POST /v1/chat/completions` | Copilot, Aider, opencode, Junie |
| `responses` | `POST /v1/responses` | Codex |
| `anthropic_messages` | `POST /v1/messages` | Claude Code |

A provider declares what it answers in `config.yaml`:

```yaml
providers:
  - key: openrouter
    protocols: [chat_completions, responses, anthropic_messages]
    anthropic_base_url: https://openrouter.ai/api
```

A pairing the endpoint cannot serve is refused before the workspace is prepared,
naming the format. `anthropic_base_url` is needed only where the Messages API
does not sit under `base_url`: Claude Code appends `/v1/messages` to the value it
receives, so it is given the endpoint root rather than the versioned path.

## Provider access

The platform never names a vendor to an agent. It resolves the active provider
and exports `RP_PROVIDER`, `RP_PROVIDER_BASE_URL`, `RP_PROVIDER_API_KEY`,
`RP_PROVIDER_PROTOCOLS`, and `RP_PROVIDER_ANTHROPIC_BASE_URL` where it applies.
Translate that into whatever the CLI reads, and clear the variable that would let
it authenticate against its own vendor instead; otherwise a run reports one
provider while the request is billed to another:

| CLI | Reads | Cleared |
|---|---|---|
| Copilot | `COPILOT_PROVIDER_BASE_URL`, `COPILOT_PROVIDER_API_KEY` | `COPILOT_GITHUB_TOKEN` |
| Aider | `OPENAI_API_BASE`, `OPENAI_API_KEY` | - |
| Codex | `CODEX_HOME/config.toml` provider block | - |
| Claude Code | `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` | `ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN` |
| opencode | generated `opencode.json` provider block | - |
| Junie | `JUNIE_HOME` model profile reading `${RP_PROVIDER_API_KEY}` | `JUNIE_API_KEY` |

Junie's profile stores `${RP_PROVIDER_API_KEY}` rather than the key: a profile
file is readable by anything that can read the session directory, and it would
otherwise travel inside an exported evidence bundle.

## Bounded turns

A CLI that streams JSON is translated into the platform's event vocabulary by a
wrapper the platform launches instead of the CLI. The wrapper writes
`events.jsonl`, mirrors a readable transcript into the terminal, forwards signals
so Stop reaches the agent, and exits with the CLI's own status. Close a turn at
the CLI's own step boundary; `plugins/agents/claude/events.py`,
`plugins/agents/opencode/events.py` and `plugins/agents/junie/events.py` each do
this for a different vocabulary. A translation that never closes a turn shows the
whole session as one unreadable step.

## 1. `plugin.yaml`

```yaml
type: agent
key: mytool
name: My CLI Tool
binary: mytool                # the executable this adapter drives
install: npm install -g mytool # shown when that executable is missing
entrypoint: plugin:Plugin
capabilities: {lsp: true, subagents: false, eval_tool: true, retrieval: true}
```

`capabilities` gate which setups the wizard offers: `s1_lsp` needs `lsp`, `s3`
needs `subagents`, `s1_eval` needs `eval_tool`, and both `s2_rag_*` profiles
need `retrieval`. The backend repeats this validation when a run is created, so
a stale or custom client cannot bypass it and silently launch an S1 fallback.
Declare a capability only if the adapter actually implements it: aider has no
MCP client and declares `retrieval: false`, so the platform refuses S2 for it
instead of running S1 under an S2 label.

`binary` is resolved on `PATH` whenever the catalogue is read. An adapter whose
executable is absent is shown as unavailable with its `install` command, and
creating or starting a run with it is refused, so a missing CLI is not recorded
as an agent failure. Installing the tool takes effect without a restart.

## 2. `plugin.py`

```python
from pathlib import Path
from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

class Plugin(AgentPlugin):
    key = "mytool"
    capabilities = {
        "lsp": True, "subagents": False,
        "eval_tool": True, "retrieval": True,
    }
    # Paths the adapter writes *inside the workspace*. The platform excludes
    # them from the captured diff: they are scaffolding, not the agent's change.
    # Omit them and `workspace_changed` can pass on your config file alone.
    workspace_artifacts = (".github/lsp.json",)

    def prepare(self, session: SessionCtx) -> None:
        # Write any config the tool needs into session.config_dir (its private
        # HOME for this session). The prompt is already at session.prompt_path.

    def command(self, session: SessionCtx) -> CommandSpec:
        return CommandSpec(
            argv=["mytool", "-p", f"@{session.prompt_path}", "--dir", str(session.workspace)],
            env=self._env(session),
            cwd=session.workspace,
        )

    def resume_command(self, session: SessionCtx, prompt_path: Path) -> CommandSpec | None:
        # Optional: continue the SAME logical session for one bounded protocol
        # reminder. Return None when the CLI has no safe resume mechanism.
        return CommandSpec(
            argv=["mytool", f"--resume={session.session_id}", "-p", f"@{prompt_path}"],
            env=self._env(session),
            cwd=session.workspace,
        )

    def events_path(self, session: SessionCtx) -> Path | None:
        # Where the tool writes structured events, if any. Return None if none.
        return None

    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo:
        # Extract tokens, model, response text, and failure flags. Fall back to
        # the terminal log when the tool has no structured events.
        return SessionInfo(tokens_input=..., tokens_output=..., model=..., response_text=...)
```

### The session env

The platform passes provider access in `session.requested_env` as three
vendor-neutral values: `RP_PROVIDER`, `RP_PROVIDER_BASE_URL` and
`RP_PROVIDER_API_KEY`. Translate them into whatever your tool expects inside
`_env()` rather than reading a vendor's own variable: the active provider is a
configuration decision (see [Extending](extending.md#model-providers)), and an
adapter that hardcodes one stops working when it changes.

The Copilot adapter maps them to `COPILOT_PROVIDER_BASE_URL`,
`COPILOT_PROVIDER_API_KEY` and `COPILOT_MODEL`, which runs the CLI against any
OpenAI-compatible endpoint without a GitHub subscription. Missing credentials
should raise with the provider named, so the operator learns what to configure.

Set `session.config_dir` as the tool's HOME if it writes global state, so
sessions never collide.

An adapter declaring `eval_tool: true` should implement `resume_command()` when
the CLI supports exact-session continuation. If the first pass omits the
mandatory self-check, the platform may use this hook once within the original
task timeout. It never starts an unbounded retry loop or changes benchmark
pass/fail semantics.

### Retrieval MCP configuration

For S2, the platform performs retrieval itself and may set
`session.mcp_config` to a standard MCP document. An adapter declaring
`retrieval: true` must either pass this configuration to its CLI or reject the
profile during compatibility checks. It must not parse benchmark-specific data
or implement a second index.

The Copilot reference adapter writes the document to its private session config
and adds `--additional-mcp-config @<path>`. The platform injects retrieved
context into `prompt.md` independently, so pre-injection still works if the
agent makes no live search calls. Never copy the MCP config into the workspace
or include it in exports; it is private execution scaffolding.

### Flags

`SessionInfo.flags` drives result classification. Recognized values:
`auth_wall`, `rate_limited`, `transport_error`, `model_mismatch`. Detect them
from the terminal log or events and the platform surfaces the right reason.

### Tools without a structured event stream

The dashboard's Agent view reads one vocabulary: `session.start`,
`user.message`, `assistant.turn_start`, `assistant.message`,
`tool.execution_start`, `tool.execution_complete`, `assistant.turn_end`,
`session.shutdown`. An adapter whose CLI reports something else translates it
rather than changing the dashboard.

Both new adapters do this in a small wrapper the platform launches instead of
the CLI: it mirrors the tool's output to the terminal, appends translated events
to `events.jsonl`, forwards signals so stopping a task stops the agent, and
exits with the tool's status.

| Adapter | Native output | Translated in |
|---|---|---|
| `codex` | JSON lines from `codex exec --json` | `plugins/agents/codex/events.py` |
| `aider` | the lines aider prints | `plugins/agents/aider/events.py` |

Record what the tool reports, at the precision it reports: aider prints token
counts humanized (`1.2k`), and its adapter documents that rather than implying
an exact figure.

## 3. Verify

```bash
cd server
uv run pytest tests/test_copilot_plugin.py   # pattern to copy for your adapter
uv run pytest tests/test_agent_adapters.py   # replayed real CLI output
uv run pytest tests/test_agent_availability.py
```

`tests/test_agent_adapters.py` replays output captured from the real CLIs
against the translation, which is what keeps the Agent view, the token
accounting and the failure flags correct when a CLI changes its output.

Then the tool appears in the New-Run wizard's "Coding Tool" step. See
`plugins/agents/copilot` as the reference implementation, and
[Extending](extending.md) for the other extension points.

Adapter acceptance must also prove conformance telemetry: excluded mechanisms
stay at zero under S1, and each declared setup can produce its corresponding
`lspActions`, `evalToolInvocations`, `subagentInvocations`, or successful S2
pre-injection evidence. A correct benchmark result alone is not proof that the
adapter implemented the setup.
