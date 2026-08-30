# Testing

`make check` runs every check below in order. CI runs the same targets, so a
change that passes locally passes there. [CONTRIBUTING.md](../CONTRIBUTING.md)
lists the commands; this page covers what each one needs and what to test for a
change of a given kind.

## Server tests

```bash
make backend
```

Python 3.12. Three markers select tests that need something the default run does
not provide:

| Marker | Needs |
|---|---|
| `integration` | PostgreSQL with pgvector |
| `data` | bootstrapped benchmark data |
| `live` | a real agent CLI and a provider key |

Retrieval runs against a real database rather than a mock. Without one, those
tests skip and the rest of the suite still runs. To include them, start pgvector
and point the suite at it:

```bash
docker run -d --name rp-test-db -p 15499:5432 \
  -e POSTGRES_DB=refactor_retrieval -e POSTGRES_USER=refactor \
  -e POSTGRES_PASSWORD=test-only pgvector/pgvector:pg16

make backend \
  RETRIEVAL_TEST_DATABASE_URL=postgresql://refactor:test-only@127.0.0.1:15499/refactor_retrieval \
  PLATFORM_TEST_DATABASE_URL=postgresql+asyncpg://refactor:test-only@127.0.0.1:15499/refactor_retrieval
```

Embeddings in tests come from `RETRIEVAL_EMBEDDER`, a `module:function` returning
an embedder. The suite injects a deterministic one, so hybrid search, fusion,
reranking and the MCP tools are exercised for real without a model server. See
[Retrieval (S2)](retrieval.md#models).

## Plugin contracts

```bash
make plugins                                  # every shipped plugin
make plugin PLUGIN=plugins/benchmarks/mine    # one of your own
```

`server/tests/test_plugin_conformance.py` runs the same checks over the shipped
plugins and over every example under `examples/plugins/`, and asserts that
deliberately broken plugins are reported.

## Dashboard

```bash
make web      # component and model tests
make types    # type check
make build    # production build
```

## Browser

```bash
make browser
```

`playwright.config.ts` starts an isolated API through `scripts/e2e_backend.py`:
its own state directory, its own port, the test fixture plugins, and no provider
key. It shares nothing with a running deployment.

The target reports one line and succeeds where Chromium cannot start — a missing
browser or a missing system library — because that is an absent dependency
rather than a failing dashboard. Install it once:

```bash
cd web && npx playwright install --with-deps chromium
```

`--with-deps` needs root. Without it, unpack the two libraries Chromium links
against but Playwright does not bundle, and point the loader at them:

```bash
cd "$(mktemp -d)"
apt-get download libgbm1 libvulkan1        # no root required
for deb in *.deb; do dpkg-deb -x "$deb" .; done
mkdir -p ~/.local/chrome-libs
cp usr/lib/x86_64-linux-gnu/libgbm.so.1* usr/lib/x86_64-linux-gnu/libvulkan.so.1* \
  ~/.local/chrome-libs/

cd -
LD_LIBRARY_PATH=~/.local/chrome-libs make browser
```

The other route is a container that already has them:

```bash
docker run --rm -it -v "$PWD":/repo -w /repo/web \
  mcr.microsoft.com/playwright:v1.58.2-noble \
  bash -c "npm ci && npx playwright test"
```

## Documentation

```bash
make docs
```

Checks every relative link, every heading anchor and every referenced figure, and
reports a figure no document references.

## What to test for a change

| Change | Test that must exist |
|---|---|
| A bug fix | One that fails without the fix |
| An evaluation metric | Its stage over a prepared workspace, passing and failing |
| An agent adapter | Its own output translated into events, and `parse_session` on an empty log |
| A benchmark | Its tasks load, its prompt renders, its pipeline scores a known result |
| An API route | Its status codes, including the refusal path |
| A dashboard view | Its rendered markup for each state the API can return |
| A schema change | A migration, and the query paths that read the column |
