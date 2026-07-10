# Evaluation

A refactoring is correct when the code still does what it did, and the change
the task asked for actually happened. Neither half is checkable by diffing text,
so every verdict here comes from executing something.

## The pipeline

Each benchmark manifest declares two lists of stages and one boolean expression:

```yaml
evaluation:
  capture: [git_diff, events_metrics, swe.codebleu]   # measure; never gate
  verify:                                             # gate
    - {preset: workspace_changed}
    - {preset: swe.prepare_candidate}
    - {preset: refactoring_miner, config: {...}}
    - {preset: java_build, config: {command_from: params.compileCommand, ...}}
  passed: "workspace_changed and refactoring_miner and java_build"
```

A stage name containing a dot is plugin-defined; everything else is a core
preset. `passed` is evaluated over the verify stages, so adding a metric can
never silently change a pass rate. Operators may retune a stage's config or
disable it from Settings; the manifest remains the source of truth for what
*can* run.

## What each stage establishes

| Stage | Kind | Establishes |
|---|---|---|
| `workspace_changed` | verify | the agent edited something at all |
| `python_tests` | verify | RefactorBench's hidden test file passes |
| `refactoring_miner` | verify | the *named* refactoring is present in the AST |
| `java_build` | verify | the project compiles and its full suite passes |
| `swe.codebleu` | capture | similarity to the reference refactoring |
| `events_metrics` | capture | tokens, context, compactions, overflows |

`refactoring_miner` and `java_build` are deliberately redundant. A build can go
green because the agent deleted the hard part; RefactoringMiner rejects that,
because the declared refactoring is not in the AST. Conversely an agent can
perform a textbook Extract Method that fails to compile. Only both together mean
what "the agent did the task" should mean.

This is not hypothetical. In a real run, the agent hit a provider error and
edited nothing at all. The untouched checkout compiled and passed the project's
entire suite:

```
workspace_changed      ok=False  No changes were made to the repository.
swe.prepare_candidate  ok=True   Prepared single-file refactoring inputs from workspace.
refactoring_miner      ok=False  Declared refactoring not detected.
java_build             ok=True   2032/2032 tests passed.
```

A test-passing harness would have scored that a success. Here it is a failure,
because two of the three gates dissent.

### Why `python_tests` is the whole verdict for RefactorBench

RefactorBench ships a hidden test per task. The task's own suite is the oracle,
exactly as the benchmark intends; the platform adds only `workspace_changed` so
that an agent which does nothing cannot pass by luck on a test that was already
green.

### CodeBLEU is a measurement, not a gate

`swe.codebleu` scores the agent's file against the dataset's reference
refactoring (`sourceCodeAfterForWhole`), blending n-gram, weighted n-gram, AST
and data-flow match. It is a **capture** stage: an agent that reaches the same
behaviour by a different route is not wrong, so a low score is a reason to read
the diff, not a verdict. It is reported per task and exported in the CSV
(`codebleu`, `codebleuSyntax`, `codebleuDataflow`).

The original study scored a snippet the agent pasted into a response envelope.
This platform has no envelope — weak models are unreliable at duplicating their
work into a side file, and the workspace is authoritative regardless — so the
candidate is read from the workspace and compared whole-file. That is the only
comparison both sides can supply honestly.

## Trusting a failure: the baseline gate

Before a `java_build` failure is attributed to an agent, the identical command,
JDK, locale and unprivileged user must build an **unmodified checkout** green.
Without this, harness defects are silently recorded as model failures. Real
examples this gate caught:

* an unset locale gave the JVM an ASCII default charset, failing suites that
  compare accented text;
* the agent ran as `root` while the build ran as `runner`, leaving undeletable
  scratch files;
* a `-Djava.io.tmpdir` override of ours broke `FilesUncheckTest`;
* **93 rows of the SWE-Refactor dataset ship a truncated build command** —
  `-Dtest='!A,!B` with no closing quote — which dies in `/bin/sh` before Maven
  starts.

The last one is now repaired at ingest, and a command the shell cannot parse
fails with `malformed_build_command` rather than being blamed on the model.

## Honesty rules the code enforces

* A stage's structured `outputs` (e.g. `testsPassed`, `testsTotal`) flow into the
  result. Nothing re-parses its own English message.
* Test counts are read only from a runner's own summary line. Maven prints
  `[INFO] 14 errors` on a *compile* failure; that is not fourteen tests.
* Cost is computed from the provider's published per-token prices. A model with
  no published price yields no cost, and a negative rate — OpenRouter's `-1`
  sentinel for "depends which model the router picks" — is not a price.
* The agent reports output tokens per message but prompt tokens and true context
  occupancy only at `session.shutdown`. Mid-run, the dashboard shows what was
  measured and says the rest is not yet reported. It does not extrapolate.
