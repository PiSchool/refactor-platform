# Example plugins

One minimal, working plugin per extension point. Copy a directory into
`plugins/<kind>/`, rename it, and edit. Each passes the contract check:

```bash
make plugin PLUGIN=examples/plugins/benchmarks/example-bench
```

| Directory | Extension point | Reference |
|---|---|---|
| `benchmarks/example-bench` | Tasks, prompt, evaluation pipeline | [Adding a benchmark](../../docs/adding-a-benchmark.md) |
| `agents/example-agent` | An AI CLI tool the platform drives | [Adding an agent tool](../../docs/adding-an-agent-tool.md) |
| `evaluation/example_metric` | One measurement any benchmark can reference | [Evaluation](../../docs/evaluation.md) |
| `lsp/example-lsp` | A language server offered to the S1+LSP setup | [Extending](../../docs/extending.md) |

Nothing here is loaded by the running platform: it discovers plugins under
`plugins/`, not `examples/`. The checks in [CONTRIBUTING.md](../../CONTRIBUTING.md)
run the same validation over both.
