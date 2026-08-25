# Documentation

| Document | Scope |
|---|---|
| [Deployment](deployment.md) | Installing the stack, remote hosts, upgrades and backups |
| [Configuration](configuration.md) | Environment variables, runtime settings, model providers, credentials |
| [Operator guide](user-guide.md) | Launching a run, watching it, acting on it, reading the result |
| [Extending](extending.md) | Benchmarks, agent tools, evaluation metrics, model providers, tasks, corpora |
| [Architecture](architecture.md) | Packages, data flow and the plugin boundary |
| [Evaluation](evaluation.md) | Stages, pass expressions, the baseline gate, and what keeps harness faults out of agent verdicts |
| [Retrieval (S2)](retrieval.md) | Chunking, indexing, hybrid search, reranking, provenance |
| [Results](results.md) | What was measured, on how many tasks, with which provenance |
| [Replication](replication.md) | Reproducing the acceptance matrix |
| [Release and versions](release.md) | Pinned versions of every component a result depends on |
| [Setup conformance](setup-conformance-results.md) | The run ids that show each setup behaved as named |
| [Requirements traceability](requirements-traceability.md) | Where each locked decision lives in the code, and what is not delivered |
| [Adding a benchmark](adding-a-benchmark.md) | The benchmark plugin contract, end to end |
| [Adding an agent tool](adding-an-agent-tool.md) | The agent adapter contract, end to end |
| [Troubleshooting](troubleshooting.md) | Recognising and resolving common failures |

Machine-readable study inputs are in [`exports/`](exports/); the figures used in
[Results](results.md) are regenerated from them by `scripts/figures.py`.

For questions use [Support](../SUPPORT.md); report vulnerabilities privately
through [Security](../SECURITY.md).

## Conventions

- Commands run from the repository root unless a guide says otherwise.
- Secrets never appear in documentation, screenshots, issues, exports or
  commits. Examples use placeholders.
- Every result states its denominator and whether the run was complete, partial,
  acceptance-only, or part of the larger study.
- Screenshots ship in a light and a dark variant and are embedded with
  `<picture>` so they follow the reader's theme. Regenerate both against a
  running stack when the UI changes:
  `cd web && node scripts/capture-screenshots.mjs`.
- Links between files in this repository stay relative, so forks and offline
  checkouts keep working.
