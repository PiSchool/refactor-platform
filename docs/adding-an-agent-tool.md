# Adding an AI CLI tool

An agent tool is a directory under `plugins/agents/<key>/` with a `plugin.yaml`
and a `plugin.py` implementing `AgentPlugin`. The platform owns the process
lifecycle (PTY, timeout, kill, logging); your adapter only declares **how to
invoke** the tool and **how to interpret** its output.

## 1. `plugin.yaml`

```yaml
type: agent
key: mytool
name: My CLI Tool
version: 1.0.0
entrypoint: plugin:Plugin
capabilities: {lsp: true, subagents: false, eval_tool: true}
models: [openrouter/free]     # suggestions shown in the wizard; free-text allowed
```

`capabilities` gate which setups the wizard offers: `s1_lsp` needs `lsp`, `s3`
needs `subagents`, `s1_eval` needs `eval_tool`.

## 2. `plugin.py`

```python
from pathlib import Path
from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

class Plugin(AgentPlugin):
    key = "mytool"
    capabilities = {"lsp": True, "subagents": False, "eval_tool": True}
    models = ["openrouter/free"]
    # Paths the adapter writes *inside the workspace*. The platform excludes
    # them from the captured diff — they are scaffolding, not the agent's change.
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

    def events_path(self, session: SessionCtx) -> Path | None:
        # Where the tool writes structured events, if any. Return None if none.
        return None

    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo:
        # Extract tokens, model, response text, and failure flags. Fall back to
        # the terminal log when the tool has no structured events.
        return SessionInfo(tokens_input=..., tokens_output=..., model=..., response_text=...)
```

### The session env

The platform passes provider credentials in `session.requested_env` (the
`OPENROUTER_*` values from `.env`). Translate them into whatever your tool
expects inside `_env()`. Copilot, for example, maps them to
`COPILOT_PROVIDER_BASE_URL` / `COPILOT_PROVIDER_API_KEY` / `COPILOT_MODEL` so it
runs BYOK against any OpenAI-compatible endpoint — no GitHub subscription.

Set `session.config_dir` as the tool's HOME if it writes global state, so
sessions never collide.

### Flags

`SessionInfo.flags` drives result classification. Recognized values:
`auth_wall`, `rate_limited`, `transport_error`, `model_mismatch`. Detect them
from the terminal log or events and the platform surfaces the right reason.

## 3. Verify

```bash
uv run pytest tests/test_copilot_plugin.py   # pattern to copy for your adapter
```

Then the tool appears in the New-Run wizard's "Coding Tool" step. See
`plugins/agents/copilot` as the reference implementation — including the PTY
spike that proved BYOK works end to end.
