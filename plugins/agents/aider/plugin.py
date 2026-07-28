"""Aider adapter (verified against aider 0.86.2).

Aider is a pair-programming CLI rather than a tool-calling agent: it edits
files through the model's reply and does not call MCP servers, so this adapter
declares no retrieval or LSP capability and the platform refuses those setups
for it instead of running a weaker session under their name.

The in-session self-check is aider's own `--auto-test`, pointed at the eval
script the platform installs, so an eval-tool run is a real feedback loop.
Aider prints the script's output without announcing the command, so the
attempts are counted from the record the eval script itself writes.

Three defaults are overridden because they would corrupt the record: automatic
commits (the platform diffs against the baseline commit), URL fetching from the
prompt, and configuration files read out of the repository under test.
Imports ONLY from app.catalog.sdk.
"""
from __future__ import annotations

import sys
from pathlib import Path

from app.catalog.sdk import AgentPlugin, CommandSpec, SessionCtx, SessionInfo

# A plugin's own modules are imported relative to it. Bare `import events`
# would collide with the other adapters, which ship a module of that name too.
from . import events as events_mod

EVAL_SCRIPT = "eval.sh"


class Plugin(AgentPlugin):
    capabilities = {"lsp": False, "subagents": False, "eval_tool": True, "retrieval": False}
    models: list[str] = []
    workspace_artifacts = (".aider*",)
    _requested_model = ""

    def _events_file(self, session: SessionCtx) -> Path:
        return session.config_dir / "events.jsonl"

    def prepare(self, session: SessionCtx) -> None:
        self._requested_model = session.model
        session.config_dir.mkdir(parents=True, exist_ok=True)
        # Neutral files: aider would otherwise read .aider.conf.yml and .env
        # from the repository under test. The config has to be a YAML mapping;
        # an empty file is rejected at startup.
        (session.config_dir / "aider.conf.yml").write_text("{}\n", encoding="utf-8")
        (session.config_dir / "aider.env").write_text("", encoding="utf-8")

    def _aider_argv(self, session: SessionCtx, prompt_path: Path, resume: bool) -> list[str]:
        argv = [
            "aider",
            "--model", f"openai/{session.model}",
            "--message-file", str(prompt_path),
            "--config", str(session.config_dir / "aider.conf.yml"),
            "--env-file", str(session.config_dir / "aider.env"),
            "--chat-history-file", str(session.config_dir / "chat-history.md"),
            "--input-history-file", str(session.config_dir / "input-history.md"),
            "--yes-always",
            "--no-auto-commits",
            "--no-dirty-commits",
            "--no-check-update",
            "--no-show-release-notes",
            "--no-analytics",
            "--no-show-model-warnings",
            "--no-detect-urls",
            "--no-gitignore",
            "--no-pretty",
            "--encoding", "utf-8",
        ]
        if session.setup.eval_tool:
            argv += ["--auto-test", "--test-cmd", f"bash {EVAL_SCRIPT}"]
        if resume:
            argv.append("--restore-chat-history")
        return argv

    def _wrapped(self, session: SessionCtx, prompt_path: Path, resume: bool) -> CommandSpec:
        argv = [
            sys.executable, str(Path(__file__).parent / "run.py"),
            "--events", str(self._events_file(session)),
            "--prompt", str(prompt_path),
            "--model", session.model,
            "--", *self._aider_argv(session, prompt_path, resume),
        ]
        return CommandSpec(argv=argv, env=self._env(session), cwd=session.workspace)

    def command(self, session: SessionCtx) -> CommandSpec:
        return self._wrapped(session, session.prompt_path, resume=False)

    def resume_command(self, session: SessionCtx, prompt_path: Path) -> CommandSpec:
        return self._wrapped(session, prompt_path, resume=True)

    def _env(self, session: SessionCtx) -> dict[str, str]:
        env = dict(session.requested_env)
        key = env.get("RP_PROVIDER_API_KEY", "").strip()
        base_url = env.get("RP_PROVIDER_BASE_URL", "").strip()
        provider = env.get("RP_PROVIDER", "provider").strip() or "provider"
        if not key:
            raise RuntimeError(f"no API key configured for provider {provider!r}; "
                               "set its API-key environment variable in .env")
        if not base_url:
            raise RuntimeError(f"no base URL configured for provider {provider!r}; "
                               "set it in config.yaml or its base-URL environment variable")
        # Credentials travel in the environment: an argv key would be visible in
        # the process table and in the recorded terminal.
        env["OPENAI_API_KEY"] = key
        env["OPENAI_API_BASE"] = base_url
        env["AIDER_ANALYTICS"] = "false"
        return env

    def events_path(self, session: SessionCtx) -> Path | None:
        path = self._events_file(session)
        return path if path.is_file() else None

    def parse_session(self, events_path: Path | None, terminal_log_path: Path) -> SessionInfo:
        parsed = events_mod.parse(events_path, terminal_log_path, self._requested_model)
        return SessionInfo(
            tokens_input=parsed["tokens_input"],
            tokens_output=parsed["tokens_output"],
            tokens_cache_read=parsed["tokens_cache_read"],
            tokens_reasoning=parsed["tokens_reasoning"],
            context_tokens=parsed["context_tokens"],
            model=parsed["model"],
            response_text=parsed["response_text"],
            readable_transcript=parsed["readable_transcript"],
            flags=set(parsed["flags"]),
            eval_tool_invocations=parsed["eval_tool_invocations"],
            retrieval_invocations=parsed["retrieval_invocations"],
        )
