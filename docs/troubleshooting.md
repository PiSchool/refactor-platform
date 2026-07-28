# Troubleshooting

Start with service state and backend logs:

```bash
docker compose ps
docker compose logs --tail=200 backend
curl -fsS http://127.0.0.1:8000/api/health
```

The health response should report the database as `ok` and the worker as
`running`, and its `retrieval` object should report the embedding model and
pgvector `ready`. When quoting it in an issue, leave out credentials, full
prompts, private repository content, retrieved chunks and unredacted event logs.

## The dashboard does not load

```bash
docker compose logs --tail=200 frontend
docker compose port frontend 3000
```

- Confirm `RP_WEB_PORT` is not already in use.
- Rebuild after frontend dependency or source changes:
  `docker compose up -d --build frontend`.
- If the frontend is healthy but API requests fail, verify the backend health
  check and the `PLATFORM_API_ORIGIN` build argument in `docker-compose.yml`.

## A rebuild appears to change nothing

Compare the running containers with the source on disk:

```bash
python3 scripts/deployment_status.py
```

- `STALE` means that image was not replaced. Rebuild it with
  `docker compose up -d --build`, and check that the changed file is not excluded
  by `.dockerignore`.
- Matching fingerprints mean the deployment carries the change, so the stale copy
  is in the browser: reload the page and compare
  **Settings → Services → Deployment** with the reported values.
- `not reporting` for the dashboard means the container predates the build stamp
  and serves no `/rp-build`. Rebuild the frontend.
- A change confined to tests does not move either fingerprint, by design.

## A benchmark stays `missing` or `provisioning`

Bootstrap needs network access and can take time:

```bash
docker compose exec backend python -m app.catalog.bootstrap refbench
docker compose exec backend python -m app.catalog.bootstrap swe
```

Then inspect Settings → Benchmarks and backend logs. A failed bootstrap writes an
error sentinel in the benchmark data volume. Fix the reported network, disk, or
upstream download issue before retrying; do not delete a populated volume unless
you intentionally want a complete re-bootstrap.

## Provider authentication or rate-limit errors

1. Confirm `.env` contains exactly one intended credential path.
2. Recreate the backend after changing `.env`:
   `docker compose up -d --force-recreate backend`.
3. Confirm Settings reports the key/token as `present`.
4. Launch one small task.

`openrouter/free` is routed and rate-limited. A `provider_error`, `auth_wall`, or
`rate_limited` result is not a benchmark failure. Use a fixed model for
repeatable comparisons.

## Runs stay queued

Only one run executes at a time. Check the Workflows page for an active run. If
no run is active but queued rows do not start, inspect backend logs and
`/api/health`. Restarting the backend reconciles orphaned running rows; it also
terminates any real task still in progress, so check before restarting.

## Live terminal disconnects

The terminal uses WebSocket while status/events use SSE. Reverse proxies must
support both long-lived response streaming and WebSocket upgrade headers. A
browser reconnect does not lose the persisted terminal log; completed sessions
remain replayable.

## S2 reports `retrieval_unavailable`

S2 fails closed and does not silently run as S1. Check each mandatory layer:

```bash
docker compose ps retrieval-db backend
docker compose logs --tail=200 retrieval-db backend
curl -fsS http://127.0.0.1:8000/api/health
docker compose exec retrieval-db \
  psql -U refactor -d refactor_retrieval \
  -c "select extversion from pg_extension where extname='vector';"
```

- `retrieval.status=error` means pgvector could not be reached or initialized.
- `modelCache=cold` before the first S2 task is normal. The backend needs
  outbound HTTPS access to download about 0.15 GB of public ONNX model files.
- An embedding-dimension mismatch means the model, configured dimension, and
  existing schema differ. Restore the matching settings or intentionally reset
  only the retrieval volume and rebuild indexes.
- Inspect the task's `retrieval/provenance.json` for index identity and parser
  fallback counts. Inspect `queries.json`, `hits.json`, and `context.md` before
  blaming the model for irrelevant context.

Embedding and query expansion run on the `ollama` service. While that service is
still pulling its weights, retrieval reports `provisioning` and S2 and S3 runs
are refused with that reason; `docker compose logs -f ollama` shows the progress.
An unreachable model server is reported as an error and no substitute model is
used. The candidate counts and `reranker_threads` in the `retrieval` section of
`config.yaml` are the tuning surface; record the values you used with the
experiment. See [Retrieval (S2)](retrieval.md).

## Java evaluation fails

- Read the raw `java_build` and `refactoring_miner` stage logs in Run detail.
- Check the task's requested JDK and the project's own compiler target; they are
  different concepts.
- Run the clean-checkout baseline described in [Replication](replication.md)
  before attributing a build failure to the agent.
- Verify Maven/Gradle, JDKs, locale, and the unprivileged `runner` identity from
  **Settings → Services** and the backend logs.

If the unchanged baseline fails under the same command, JDK, locale, and user,
the result is a harness/dataset failure—not an agent verdict.

## Python evaluation fails before tests run

RefactorBench tasks can target older Python AST APIs. Confirm the task uses the
`py39_ast` compatibility shim declared in the plugin and inspect the raw
`python_tests` log. Distinguish import/setup errors from assertion failures.

## Disk usage grows

The largest consumers are benchmark data, repository mirrors, retained task
workspaces, terminal logs, Java dependency caches, S2 ONNX models, and pgvector
code indexes.

- Disable **Keep task workspaces** if post-run browsing is unnecessary.
- Lower the retention cap for old artifact trees.
- Use `docker system df` to inspect Docker storage.
- Do not remove named volumes unless you accept losing the local database,
  benchmark bootstrap data, or run artifacts.

## Resetting local demo state

`docker compose down` preserves data. The following is destructive:

```bash
docker compose down -v
```

It deletes the platform database, outputs, S2 indexes/model cache, repository
data, and bootstrap state.
Use it only for an intentional clean-room reinstall and never as a routine fix.

## Still stuck?

Read [SUPPORT.md](../SUPPORT.md) and open a minimal, redacted issue with the
branch/commit, operating system, Docker versions, benchmark/setup, expected
behavior, actual behavior, and relevant log excerpts.