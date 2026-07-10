# Architecture

The platform separates three concerns that the original POC entangled:
**what to run** (benchmarks), **what runs it** (agent tools), and **how a run
is executed and judged** (the platform core). The first two are plugins; the
third is fixed platform machinery that plugins configure but never replace.

## The SDK boundary

`server/app/catalog/sdk.py` is the entire plugin-facing surface. Plugins import
from it and nothing else in `app.*`; `tests/test_catalog.py` asserts this. This
is what makes the platform a *product* rather than a benchmark harness: the core
has zero references to "refbench", "swe", or "copilot".

The SDK defines data contracts (`TaskDef`, `WorkspaceSpec`, `CommandSpec`,
`SessionCtx`, `SessionInfo`, `EvalContext`, `StageResult`, `EvalOutcome`,
`SetupProfile`) and three plugin ABCs (`AgentPlugin`, `BenchmarkPlugin`,
`LSPPlugin`).

## Layers

| Package | Responsibility |
|---|---|
| `catalog/` | Discover plugins from `plugins/`, validate manifests, sync catalog rows, bootstrap benchmark data. Invalid plugins are collected into an error list — never crash the platform. |
| `execution/` | `pty_host` (owned PTY), `workspace` (materialize + diff), `setups` (the 4 profiles), `taskloop` (per-task orchestration), `worker`/queue (sequential runs), `evaltool` (in-session self-check installer). |
| `evaluation/` | `engine` resolves an ordered stage list, runs each over a shared `EvalContext`, and computes `passed` from a boolean expression over stage names. `presets/` holds the reusable core stages. |
| `realtime/` | In-process `hub` pub/sub. WS streams terminal bytes; SSE streams status/events. No DB polling. |
| `results/` | Deterministic ZIP export, import, and run retention. |
| `api/` | Thin FastAPI routers; serializers emit camelCase for the web app. |

## Execution model

- **Owned PTY, not tmux.** The platform calls `pty.openpty()` and appends every
  byte to `terminal.log`. That file *is* the live source (tailed to the WS) and
  the replay source. Completion = process exit. Timeout = `killpg`. There is no
  separate "runner exit code" channel and no reconstructed transcript.
- **Sequential queue.** One run at a time (`execution/worker.py`), so resource
  contention and Java builds never overlap.
- **Clean workspaces.** `git` provider archives from a bare mirror at a pinned
  ref; `snapshot` copies a data directory. Both end with a fresh `git init`
  baseline so no upstream history leaks the answer.

## Setups (platform core)

Setups are **not** plugins — they are four fixed profiles in
`execution/setups.py`. A plugin only *declares compatibility* (`setups:` in its
manifest) and *may contribute a prompt block*.

| Setup | Adds |
|---|---|
| `s1` | Baseline: agent + workspace. |
| `s1_lsp` | Language-server config handed to the agent (via an `LSPPlugin`). |
| `s1_eval` | An in-workspace `eval.sh` the agent may call to self-check. **In-session only** — the platform never drives feedback rounds. |
| `s3` | Sub-agent delegation enabled (agent-native), with a guiding prompt block. |

## Evaluation pipeline

`evaluation/engine.py` builds an ordered stage list from the benchmark manifest.
A stage name containing `.` is a plugin-defined stage (`swe.prepare_candidate`);
otherwise it is a core preset (`workspace_changed`, `python_tests`,
`java_build`, `refactoring_miner`, `git_diff`, `events_metrics`,
`file_artifact`). Each stage returns a `StageResult`; `passed` is a boolean
expression over stage names (e.g. `"refactoring_miner and java_build"`). Stages
share state through `EvalContext.shared`, which is how a benchmark stage feeds
inputs to a generic core stage (swe writes `rm_args` for `refactoring_miner`).

This is why "refbench and swe are plugins that configure the platform's generic
capabilities": each benchmark picks core capture/verify stages, supplies its own
where needed, and declares the pass expression — no benchmark logic lives in the
core.

Operators may retune a stage's config, disable a stage, or replace the `passed`
expression from Settings. Those edits are stored as overrides and merged at run
time (`effective_pipeline`); the manifest remains the source of truth for which
stages *can* run.

## Data flow of one task

```
workspace.prepare ─▶ prompt (hook or template + setup.prompt_block)
   ─▶ agent.prepare/command ─▶ run_pty (terminal.log)
   ─▶ agent.parse_session ─▶ workspace.capture_diff
   ─▶ evaluation.evaluate ─▶ persist TaskResult + artifacts
```

Artifacts written per task: `prompt.md`, `response.md`, `diff.patch`,
`terminal.log`, `transcript.txt`, `events.jsonl` (agent-native),
`eval/<stage>.log` (raw build/test output), and `workspace_meta.json`
(baseline sha, changed files).

## Invariants worth knowing

These are not incidental; each was a bug that made the platform lie about an
agent, and each has a regression test.

- **Nothing blocks the event loop.** Evaluation shells out to `mvn`/`pytest`
  for minutes; it runs in a thread. The SSE tailer reads only the bytes
  appended since its last tick. File reads and toolchain probes are off-loop.
  A blocked loop stalls every request and surfaces as `socket hang up`.
- **The agent and the evaluation build share one unprivileged identity**
  (`runner`, `execution/sandbox.py`). As root, suites that assert on permission
  denial fail on an *unmodified* checkout; and a root agent leaves scratch in
  `/tmp` the build cannot delete.
- **Platform scaffolding never enters the diff.** `eval.sh` and the agent's LSP
  config land after the baseline commit; they are added to
  `.git/info/exclude`, so `git add -A` cannot sweep them in and
  `workspace_changed` cannot pass on them alone.
- **Reading the workspace never mutates it.** The live diff stages into a
  throwaway `GIT_INDEX_FILE`; repo status uses `git status --porcelain`.
- **The prompt artifact is the exact bytes handed to the agent** (`-p @prompt.md`).

Before trusting any `java_build` verdict, confirm the unmodified checkout builds
green — see the *baseline gate* in [replication.md](replication.md).
