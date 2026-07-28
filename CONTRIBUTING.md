# Contributing

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md), not
in an issue. Usage questions go to [SUPPORT.md](SUPPORT.md). Participation is
under the [Code of Conduct](CODE_OF_CONDUCT.md).

## What you can extend

Four extension points need no change to the platform's own code. Each is a
directory holding `plugin.yaml` and one Python module, dropped into `plugins/`.

| Add | Directory | Copy from | Reference |
|---|---|---|---|
| A benchmark: tasks, prompt, evaluation pipeline | `plugins/benchmarks/<id>/` | [`examples/plugins/benchmarks/example-bench`](examples/plugins/benchmarks/example-bench) | [Adding a benchmark](docs/adding-a-benchmark.md) |
| An agent CLI | `plugins/agents/<id>/` | [`examples/plugins/agents/example-agent`](examples/plugins/agents/example-agent) | [Adding an agent tool](docs/adding-an-agent-tool.md) |
| An evaluation metric | `plugins/evaluation/<id>/` | [`examples/plugins/evaluation/example_metric`](examples/plugins/evaluation/example_metric) | [Evaluation](docs/evaluation.md) |
| A language server | `plugins/lsp/<id>/` | [`examples/plugins/lsp/example-lsp`](examples/plugins/lsp/example-lsp) | [Extending](docs/extending.md) |

A model provider is an entry in `config.yaml` and its key in `.env`; see
[Extending](docs/extending.md#model-providers).

Two rules the platform enforces, not conventions:

- A plugin imports the contracts from `app.catalog.sdk` and nothing else from
  `app.*`. Each plugin's modules are private to it, so two plugins may ship a
  module of the same name.
- The core names no benchmark, agent, provider or metric.

## Validate your plugin

```bash
make plugin PLUGIN=plugins/benchmarks/mine
```

It loads the directory the way the platform does and reports every violation at
once: the manifest, the entrypoint, the declared executable, the tasks, the
prompt values the template must substitute, the metrics referenced, the verdict
rule, and the session contract an adapter has to satisfy. An `error` will not
load or will fail during a run; a `warning` will load and mislead.

## Run the checks

```bash
make install     # server and dashboard dependencies
make check       # everything below, in order
```

| Command | Runs |
|---|---|
| `make backend` | Server tests |
| `make plugins` | Every shipped plugin against the contracts |
| `make web` | Dashboard tests |
| `make types` | Dashboard type check |
| `make build` | Dashboard production build |
| `make browser` | The dashboard in a real browser against a real API |
| `make docs` | Every link, anchor and figure in the documentation |

CI runs the same targets. [docs/testing.md](docs/testing.md) covers the database
the retrieval tests use, the browser suite in a container, and what to test for a
change of each kind.

## Submit

1. Branch from `main`, one purpose per branch.
2. Add or change tests with the behaviour. A bug fix carries the test that fails
   without it.
3. Update the documentation the change makes wrong.
4. Run `make check`.
5. Read your own diff for credentials, machine paths, benchmark data and
   generated artefacts. `.env`, `data/` and `.e2e/` are ignored; keep them so.
6. Open a pull request.

Keep result and figure changes in their own commit, with the export they were
computed from. Regenerate figures rather than editing them, and never commit one
appearance without the other:

```bash
uv run --with matplotlib --no-project python scripts/figures.py   # charts, from docs/exports/csv
cd web && node scripts/capture-screenshots.mjs                    # dashboard, both themes
```

A third-party tool or dataset needs distribution terms compatible with this
repository. Download it in a bootstrap step and link its license; do not commit
data whose redistribution is unclear.
