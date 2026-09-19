# Deployment

Refactor Platform ships as a three-service Docker Compose stack:

- `frontend`: Next.js dashboard and reverse proxy for `/api` and `/ws`;
- `backend`: FastAPI, the sequential worker, PTY host, plugin runtime, and the
  complete Python/Java evaluation and retrieval toolchain;
- `retrieval-db`: internal PostgreSQL 16 + pgvector storage for normalized run
  state, settings, S2 code chunks, and embeddings (no published host port).

PostgreSQL is the structured source of truth in Compose. Artifacts, models,
retrieval indexes, and benchmark data live in named volumes. SQLite is limited
to direct-backend development and isolated tests.

Agent processes are supervised directly under a platform-owned Linux PTY rather
than tmux. Every byte is first appended to the session log and then published
with its byte offset; WebSocket clients replay and resume against that durable
log. This provides deterministic ownership, reconnect, and final scrollback
without a second terminal-session manager.

The stack has no application-level authentication and the lock screen is
presentation only. Both host mappings default to loopback. To reach it from
another machine, forward the port over SSH:

```bash
ssh -L 3000:127.0.0.1:3000 user@host
```

Publishing it to a network requires a reverse proxy that provides TLS and
authentication, and the hardening below.

## Requirements

- Docker Engine with the Compose v2 plugin;
- an API key for one of the model providers declared in `config.yaml`;
- distinct random retrieval writer and read-only passwords, without which
  Compose refuses to start;
- outbound network access during image build and benchmark bootstrap.

Disk is the resource that runs out first: images, JDKs, benchmark repositories
and build caches together occupy on the order of tens of gigabytes, and Java
builds are the memory-hungry part of a run.

S2 and S3 search with the models named in `config.yaml`, served by the `ollama`
service. Its first start pulls several gigabytes of weights, during which those
setups are refused and everything else works; see [Retrieval (S2)](retrieval.md).

## Install

```bash
git clone https://github.com/PiSchool/refactor-platform.git refactor-platform
cd refactor-platform
cp .env.example .env
chmod 600 .env
```

Edit `.env` and configure provider access:

```dotenv
# The provider to use, and its key. config.yaml declares the endpoints.
RP_PROVIDER=openrouter
OPENROUTER_API_KEY=REPLACE_ME

# Required for every Compose deployment; internal database only
RETRIEVAL_DB_PASSWORD=REPLACE_WITH_A_RANDOM_VALUE
RETRIEVAL_DB_READER_PASSWORD=REPLACE_WITH_A_DIFFERENT_RANDOM_VALUE
```

The dashboard loads the selected provider's catalogue and offers every model
with text output and tool support; the wizard also accepts a model id typed by
hand, and each run persists the model it actually used. Adding a provider is an
entry in `config.yaml` and a key here; see [Extending](extending.md#model-providers).

See [Configuration](configuration.md) for all variables and credential-handling
rules.

## Start and verify

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

When the backend is healthy, open <http://localhost:3000>. The backend port is
published on loopback only at <http://127.0.0.1:8000> for local diagnostics.

```bash
curl -fsS http://127.0.0.1:8000/api/health
```

Expected shape:

```json
{"status":"ok","db":"ok","worker":"running","retrieval":{"status":"ready","embeddingModel":"hf.co/nomic-ai/nomic-embed-code-GGUF:Q4_K_M","embeddingsServedBy":"http://ollama:11434"}}
```

`retrieval.status` may initially be `configured` until the first health probe
creates the pgvector schema. On a first start it reads `provisioning` while the
model server pulls the study's weights: the platform is up and S1 runs proceed,
S2 and S3 runs are refused until the pull finishes. `docker compose logs -f
ollama` shows the progress.

Operator readiness fails with `503 retrieval_unavailable` when the configured
retrieval database cannot be probed. This keeps the dashboard and worker behind
the same fail-closed service gate as S2 instead of accepting a partially broken
deployment.

### Confirm what is deployed

A container that was not replaced looks exactly like one that was. Both images
record what they were built from, and the running deployment is compared with the
source on disk by:

```bash
python3 scripts/deployment_status.py
```

```
component  running        working tree   verdict
backend    0d280aa01c4f   0d280aa01c4f   matches the working tree
dashboard  4cf85f278c59   4cf85f278c59   matches the working tree
```

`STALE` means the image is older than the source; rebuild with
`docker compose up -d --build`. The exit status is non-zero when any component is
stale, so a deployment step can gate on it. The same values appear under
**Settings → Services → Deployment**, and the backend's is in `GET /api/health`
under `build`.

A revision is optional and is reported next to the fingerprint. Set
`RP_BUILD_REV` in `.env`, or in the environment when your Compose interpolates
from the shell:

```bash
RP_BUILD_REV=$(git rev-parse --short HEAD) docker compose up -d --build
```

It is read at runtime as well as at build time, so changing it takes a restart
rather than a rebuild.

To publish the dashboard on another host port:

```bash
RP_WEB_PORT=8787 docker compose up -d
```

Persist `RP_WEB_PORT` in the protected deployment environment when it should
survive shell sessions.

## Bootstrap benchmark data

The backend starts missing benchmark bootstraps in background threads on boot.
Readiness and errors are visible under **Settings → Benchmarks** and in
`GET /api/catalog`.

To run bootstrap synchronously and see its complete output:

```bash
docker compose exec backend python -m app.catalog.bootstrap refbench
docker compose exec backend python -m app.catalog.bootstrap swe
```

You can also request background bootstrap through the loopback API:

```bash
curl -X POST http://127.0.0.1:8000/api/benchmarks/refbench/bootstrap
curl -X POST http://127.0.0.1:8000/api/benchmarks/swe/bootstrap
```

Bootstrap is idempotent after the plugin reaches `ready`. Data is stored in the
`refbench-data` and `swe-data` named volumes. Do not remove those volumes during
a normal upgrade.

## Remote-host hardening

For a single-host deployment such as EC2:

1. Restrict SSH to trusted source addresses and use key-based login.
2. Keep `RP_API_BIND=127.0.0.1`.
3. Put the frontend behind a VPN or reverse proxy that provides TLS and real
   authentication. If temporarily exposing a host port, restrict the security
   group/firewall to known addresses.
4. Use a dedicated, least-privilege provider key. Do not attach broad AWS
   credentials or the Docker socket to the backend.
5. Store `.env` with mode `600`, or inject secrets from a proper secret manager.
6. Back up the platform data volume before database or deployment changes.
7. Back up/protect the `retrieval-data` volume as repository source; it contains
   indexed chunks and embeddings.
8. Review model-provider data retention before evaluating private repositories.

The backend container executes untrusted agent/build workloads. Do not colocate
the demo with unrelated sensitive services. Read [SECURITY.md](../SECURITY.md)
for the full threat model.

## Track a second upstream repository

A deployment checkout can keep its own remote while adding another repository
(for example the Pi School one) as an update source. This is safer than
overwriting remotes before reviewing branch differences:

```bash
cd ~/refactor-platform
git remote -v
git remote add pischool git@github.com:PiSchool/refactor-platform.git
git fetch pischool refactor-demo
git log --oneline HEAD..pischool/refactor-demo
```

If `pischool` already exists, use `git remote set-url pischool ...` instead of
adding it. Use a read-only GitHub deploy key on a server that only needs to pull.
Do not copy a developer's private key to the host and do not store deploy keys in
the repository or a tracker.

After reviewing the displayed commits and confirming the worktree is clean:

```bash
git pull --ff-only pischool refactor-demo
docker compose up -d --build
```

`--ff-only` intentionally refuses divergent history. Resolve divergence in a
normal reviewed branch/PR; do not force-reset a deployment containing unpushed
work.

## Upgrade safely

An upgrade restarts the backend and therefore terminates an active agent task.
Check the Workflows page or API before proceeding:

```bash
curl -fsS http://127.0.0.1:8000/api/runs
git status --short
git fetch origin main
git log --oneline HEAD..origin/main
```

When no task is active and local changes have been reviewed:

```bash
git pull --ff-only origin main
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1:8000/api/health
python3 scripts/deployment_status.py
```

Substitute the remote and branch if you track a different upstream.

Database migrations and plugin catalog synchronization run during backend
startup. Queued runs remain durable. A task that was running during an
unexpected restart is reconciled as an error rather than silently resumed.

Frontend-only changes can be deployed without interrupting the worker:

```bash
docker compose up -d --no-deps --build frontend
```

## Stop, remove, and preserve data

```bash
docker compose down        # stop; named volumes remain
docker compose down -v     # destructive: also deletes S2 indexes/model cache
```

Never use `-v` as a routine upgrade step. See [Troubleshooting](troubleshooting.md)
for recovery guidance.

For S2 model downloads, pgvector checks, and thread tuning, see
[Retrieval (S2)](retrieval.md).
