# Setup conformance results

Real-provider acceptance matrix results from 21 July 2026 validate
execution-regime wiring, evidence capture, and export integrity. They are not a
model-quality comparison: `openrouter/free` may route requests across different
free models over time.

## Campaign controls

- Agent backend: GitHub Copilot CLI through OpenRouter BYOK.
- Requested model for every row: `openrouter/free`.
- Retrieval execution: CPU only.
- One pinned smoke task per benchmark; one task per run.
- Runs executed sequentially through the durable worker.
- Acceptance requires `setupCompliance=conformant`, not a passing benchmark
  result. Benchmark pass/fail remains the measured agent outcome.

## Accepted evidence set

| Benchmark | Setup | Run ID | Benchmark outcome | Setup evidence |
|---|---|---|---|---|
| RefactorBench | S1 | `5efebb1fec374f99bc8803773aa21019` | Failed: `test_failed` | Conformant baseline; no optional mechanism observed |
| RefactorBench | S1-LSP | `85a317304562458ca6a22ba7e6196653` | Failed: `apply_failed` | `lspActions=1` |
| RefactorBench | S1-eval | `257576c544064398a9ef1a634d19ddd5` | Failed: `test_failed` | `evalAttempts=3`, `evalToolInvocations=4` |
| RefactorBench | S3 | `04724468702449589ebba9f2c2fc2f7f` | Failed: `test_failed` | `subagentInvocations=1` |
| RefactorBench | S2-naive | `abae0d44b61147e6b6fdd2993bd8ebf0` | Passed | Context pre-injected; naive index; 12 hits |
| RefactorBench | S2-AST | `4a1be6e6a4a4445cb406817201358f44` | Passed | Context pre-injected; AST index; 12 hits |
| SWE-Refactor | S1 | `b365c15974784ecfab2ad6dc22ecff1b` | Passed | Conformant baseline; no optional mechanism observed |
| SWE-Refactor | S1-LSP | `caaff7edc1714843a6b1a0445fe091c9` | Failed: `apply_failed` | `lspActions=1` |
| SWE-Refactor | S1-eval | `ad2dea3a66724bddb6369436877a31ce` | Passed | `evalAttempts=1`, `evalToolInvocations=3` |
| SWE-Refactor | S3 | `eb51607fe4e44288ac2e09bc1d6c7d75` | Passed | `subagentInvocations=1` |
| SWE-Refactor | S2-naive | `f9492bdb7c8a48b9b09eba8be3a2f0e5` | Failed: `apply_failed` | Context pre-injected; naive index; 12 hits |
| SWE-Refactor | S2-AST | `1c5822c8ad87434491782931594360bd` | Failed: `apply_failed` | Context pre-injected; AST index; 12 hits |

Mixed benchmark outcomes are expected in an evaluation harness and are not
setup failures. For example, the accepted SWE S1-eval row passed
RefactoringMiner and all `2032/2032` Java tests, while several other conformant
rows produced invalid agent patches and were recorded as failures.

## Artifact and export verification

For every accepted row, live verification confirmed:

- a non-empty terminal replay through the transcript API;
- prompt, response, diff, native `events.jsonl`, and evaluation artifacts;
- persisted token, model, timing, and setup-compliance metrics;
- a valid ZIP containing `summary.json`, `results.csv`, prompt, diff, terminal,
  and events evidence;
- no private Copilot-home files in the ZIP other than the required native
  `events.jsonl`.

## Excluded attempts

The following attempts remain retained for audit but are not accepted matrix
rows because the model ignored a mandatory setup mechanism:

| Benchmark | Setup | Run ID | Exclusion reason |
|---|---|---|---|
| SWE-Refactor | S1-eval | `ec272e9fbdea4a2a851e7468ddcc8ab9` | `setup_not_exercised`; no eval invocation |
| RefactorBench | S1-eval | `c38e0ac69e9c43ea8e67989a195c6814` | `setup_not_exercised`; no eval invocation |

The execution engine now gives S1-eval a single bounded same-session
continuation when the first pass omits `eval.sh`. This improves protocol
compliance without changing benchmark correctness or allowing unbounded model
usage.

Replication procedure and acceptance fields are in [Replication](replication.md).