# Release and versions

A pass rate is a statement about a whole stack, not about a model. The same
prompt against the same model returns a different verdict if the agent CLI, the
language server, the chunker or the benchmark data moved underneath it. This
page names every version that decides what a run does, so a result can be tied
to something specific.

## This release

| | |
|---|---|
| Platform version | `1.0.0` |
| Git tag | `v1.0.0` (also tagged `emnlp2026-camera-ready`) |
| Citation | [`CITATION.cff`](../CITATION.cff) |

The platform reports its own identity at runtime on `/api/health` and in
Settings → Services: a `revision` and build time stamped into the image, plus a
`fingerprint` hashing the server package, the plugins directory and
`config.yaml`. Two deployments serving the same fingerprint run the same code,
whatever their tags say; `scripts/deployment_status.py` compares a checkout
against a running host.

## Pinned by the build

Everything below is fixed in `docker/backend.Dockerfile`,
`docker/frontend.Dockerfile` or `docker-compose.yml`. Base images and the Node
tarball are pinned by digest or checksum, not by tag.

| Component | Version |
|---|---|
| Base image (backend) | `ubuntu:22.04`, by sha256 digest |
| Base image (frontend) | `node:24-slim`, by sha256 digest |
| Postgres + pgvector | `pgvector/pgvector:pg16`, by sha256 digest |
| Ollama | `ollama/ollama:0.32.4`, by sha256 digest |
| Node | `24.18.0`, verified by sha256 |
| Python | `3.12` |
| Server dependencies | `server/uv.lock` (`uv sync --frozen`) |
| Dashboard dependencies | `web/package-lock.json` (`npm ci`) |
| CodeBLEU | `codebleu==0.7.0`, `tree-sitter==0.22.3`, `tree-sitter-java==0.21.0` |
| Eclipse JDT.LS | `1.61.0-202608141332` |
| Chunker | `cpu-s2-v3` (`CHUNKER_VERSION`, part of the index identity) |

### Agent CLIs

Overridable per build with the named `ARG`, so an operator can move one
deliberately. Whatever is installed, the platform records the version each run
actually invoked as `agentVersion` in that run's telemetry.

| Agent | Version | Build argument |
|---|---|---|
| GitHub Copilot CLI | `1.0.80` | `COPILOT_CLI_VERSION` |
| OpenAI Codex CLI | `0.149.1` | `CODEX_CLI_VERSION` |
| Claude Code | `2.1.241` | `CLAUDE_CODE_VERSION` |
| opencode | `1.18.22` | `OPENCODE_VERSION` |

### Retrieval models

Declared in `config.yaml` under `retrieval`. A model name here is part of the
index identity, so changing one rebuilds the index rather than reinterpreting
vectors produced by a different encoder.

| Role | Model |
|---|---|
| Embedding | `hf.co/nomic-ai/nomic-embed-code-GGUF:Q4_K_M`, 3584 dimensions |
| Query expansion | `qwen2.5-coder:7b-instruct` |
| Cross-encoder reranker | `Xenova/ms-marco-MiniLM-L-6-v2` |

### Benchmark data

Fetched once, ahead of runs, and pinned by source rather than by date.

| Benchmark | Source |
|---|---|
| RefactorBench | `github.com/microsoft/RefactorBench` |
| SWE-Refactor | Zenodo record `17655592` |
| RefactoringMiner | `3.0.10`, shipped inside the SWE-Refactor archive |

## Model identifiers

Model strings are routed through OpenRouter and resolve to whatever that
provider currently serves under the name; providers re-point a name at a new
checkpoint without renaming it. The platform records the string it was given and
the provider's reported usage per task, which is what a rerun can be compared
against — it cannot pin a hosted checkpoint, and neither can any harness that
calls a hosted API.

The study reported in the paper used `qwen3.6-flash`, `minimax-m3`,
`kimi-k2.6`, `deepseek-v4-pro` and `gpt-5-mini`, all through OpenRouter.

## What this release cannot reconstruct

Stated plainly, because a version page that overclaims is worse than none.

- **The study runs predate the agent-version capture.** `agentVersion` is
  recorded for runs made with this release; the campaign in the paper was
  executed before that field existed, so the exact Copilot CLI build behind
  those numbers is not recoverable. The pins above make future reproductions
  deterministic; they do not retroactively identify what produced the archive.
- **Hosted model checkpoints are not pinned**, for the reason above.
- **One archived run's task-level record is missing.** The `kimi-k2.6` S1
  descriptive rerun reported in the paper has no per-task export; the archived
  run under that configuration is the earlier one. See
  [`results.md`](results.md).

## Cutting the next release

1. Update `version` in `server/pyproject.toml` and in `CITATION.cff`.
2. Refresh the tables above if any pinned version moved.
3. Tag the commit and push the tag:
   `git tag -a v1.1.0 -m "..." && git push origin v1.1.0`.
4. Build with `RP_BUILD_REV=$(git rev-parse HEAD)` so the image stamps the
   revision it was built from.
