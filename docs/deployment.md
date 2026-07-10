# Deployment

Two services, one command. The dashboard is the only thing that needs a public
port; the API is reached over the compose network.

## Requirements

* Docker with Compose v2
* ~20 GB free disk (JDK + Maven cache + benchmark repositories)
* 8 GB RAM (16 GB if you run Java builds and a language server together)
* An OpenAI-compatible API key. The reference configuration uses OpenRouter
  BYOK; `openrouter/free` runs the whole platform at zero cost.

No GPU. No database server. Nothing is downloaded at task time.

## Run it

```bash
git clone https://github.com/aziz0220/coderefactor-demo.git
cd coderefactor-demo
cp .env.example .env          # then put your key in OPENROUTER_API_KEY
docker compose up -d --build
```

The dashboard is on <http://localhost:3000>. To serve it elsewhere, set
`RP_WEB_PORT` — nothing in the compose file is deployment-specific:

```bash
RP_WEB_PORT=8787 docker compose up -d
```

`RP_API_BIND` defaults to `127.0.0.1`, so the API is not published to the world.
Override it only if you intend to expose it.

## Bootstrap the benchmark data

Benchmarks declare their own data bootstrap; the platform never fetches anything
during a task. From **Settings → Benchmarks**, or:

```bash
curl -X POST localhost:8000/api/benchmarks/refbench/bootstrap
curl -X POST localhost:8000/api/benchmarks/swe/bootstrap
```

RefactorBench clones its 100 task repositories; SWE-Refactor downloads the
dataset and RefactoringMiner. Both are idempotent, and `dataState` in
`/api/catalog` reports readiness.

## Secrets

`.env` is gitignored and never baked into an image. On a remote host, write it
over `ssh` rather than committing it, and keep it `chmod 600`. When cloning a
private repository onto a server, forward your agent (`ssh -A`) instead of
copying a private key onto the machine.

## The hosted demo

A single `t3.xlarge` runs the whole stack — agent PTY sessions, Java builds, and
the language server — with `RP_WEB_PORT=8787` and only that port open in the
security group. Runs execute one at a time (the queue is sequential), so a
`t3.xlarge` is sized for a demo, not for a campaign.

To rebuild after a push:

```bash
cd ~/coderefactor-demo && git pull && docker compose up -d --build
```

## Upgrading in place

The database migrates on boot and orphaned `running` runs are reconciled to
`error` at startup, so a restart is safe — **except** that it kills whatever is
mid-run. Check first:

```bash
curl -s localhost:8000/api/runs | grep -c '"status": "running"'
```

Deploy the frontend alone (never interrupts a run) with:

```bash
docker compose up -d --no-deps --build frontend
```
