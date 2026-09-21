# Evaluation

A refactoring is correct when the code still does what it did, and the change the
task asked for actually happened. Neither half is checkable by diffing text, so
every verdict here comes from executing something.

## The pipeline

A benchmark's manifest declares the pipeline; the platform runs it in this order.

| Step | What it is |
|---|---|
| prepare | The benchmark's own step, before anything measures. It puts the workspace into the shape its metrics expect and publishes what they read. Optional. |
| capture | Metrics that record numbers and evidence. They never fail a task. |
| verify | Metrics that can fail a task, in order. |
| verdict | A boolean expression over the verify stages. |

```yaml
evaluation:
  prepare: prepare_candidate        # implemented by this benchmark's plugin.py
  capture:
    - git_diff
    - events_metrics
    - {preset: codebleu, config: {language: java}}
  verify:
    - workspace_changed
    - {preset: refactoring_miner, config: {binary_from_data: RefactoringMiner/bin/rm}}
    - {preset: java_build, config: {command_from: params.compileCommand}}
  passed: "workspace_changed and refactoring_miner and java_build"
```

A stage is written as a bare id, or as `{preset: id, config: {...}}` when it takes
options. An empty `passed` means every verify stage must pass.

Adding a metric to `capture` cannot change a pass rate, because `passed` is
evaluated over `verify` alone. From Settings an operator may retune a stage's
options, switch a stage off, add any installed metric, or replace the verdict
rule; a rule that names a metric this deployment does not have is dropped rather
than failing every task.

## One metric, one directory

**An evaluation plugin provides exactly one metric, and the metric's id is the
plugin's directory name.**

```
plugins/evaluation/java_build/
  plugin.yaml     # identity: key (= directory = metric id), name
  plugin.py       # class Plugin(EvaluationPlugin)
```

Ids are therefore bare (`java_build`, `codebleu`, `pytest_suite`) and unique by
construction. A benchmark **references** a metric by id and configures it; it
never defines one. The loader refuses a benchmark that tries, and names the
directory to move the measurement to. There is no second place a metric can live.

## What ships

| Metric | Gates | Establishes | Needs |
|---|---|---|---|
| [`workspace_changed`](../plugins/evaluation/workspace_changed/plugin.py) | yes | the agent edited something at all | nothing |
| [`refactoring_miner`](../plugins/evaluation/refactoring_miner/plugin.py) | yes | the *named* refactoring is present, per RefactoringMiner | the detector in the benchmark's data |
| [`java_build`](../plugins/evaluation/java_build/plugin.py) | yes | the project compiles and its own suite passes | a JDK and Maven or Gradle |
| [`python_tests`](../plugins/evaluation/python_tests/plugin.py) | yes | one test file shipped with the benchmark passes | that file in the benchmark's data |
| [`pytest_suite`](../plugins/evaluation/pytest_suite/plugin.py) | yes | the repository's own suite still passes | pytest |
| [`pyrefactor`](../plugins/evaluation/pyrefactor/plugin.py) | yes | the named Python refactoring is present in the parse tree | nothing |
| [`file_artifact`](../plugins/evaluation/file_artifact/plugin.py) | yes | the agent wrote the file it was asked to write | a path from the benchmark |
| [`codebleu`](../plugins/evaluation/codebleu/plugin.py) | no | similarity to a reference version of the file | the `codebleu` library, and a reference |
| [`git_diff`](../plugins/evaluation/git_diff/plugin.py) | no | records the diff and its size | nothing |
| [`events_metrics`](../plugins/evaluation/events_metrics/plugin.py) | no | records tokens, model and self-check iterations | an agent session |

A metric that cannot run here says so: on the Plugins screen before a run, and
in its stage result during one. It never reports success it did not establish.

`python_tests` and `pytest_suite` are different measurements. The first runs one
file that ships with the benchmark, outside the repository, so the agent cannot
weaken it; the second runs the tests inside the repository under test, which is
what catches a refactoring that changes behaviour.

## Two gates, neither sufficient

`refactoring_miner` and `java_build` overlap deliberately. A build can go green
because the agent deleted the hard part; RefactoringMiner rejects that, since the
declared refactoring is not in the tree. An agent can also perform a textbook
Extract Method that fails to compile. Both have to hold.

In one run the agent hit a provider error and edited nothing. The untouched
checkout compiled and passed the project's entire suite:

```
prepare_candidate    ok=True   Prepared single-file refactoring inputs from workspace.
workspace_changed    ok=False  No changes were made to the repository.
refactoring_miner    ok=False  Declared refactoring not detected.
java_build           ok=True   2032/2032 tests passed.
```

A harness that checks only the test suite would have scored that a success.

For RefactorBench the hidden test file is the oracle, exactly as that benchmark
intends; the platform adds only `workspace_changed`, so an agent that does
nothing cannot pass on a test that was already green.

`codebleu` is recorded, never gating: an agent that reaches the same behaviour by
another route is not wrong, so a low score is a reason to read the diff. It is
exported per task as `codebleu`, `codebleuSyntax`, `codebleuDataflow`. The study
scored a snippet the agent pasted into a response envelope; this platform has no
envelope, so the candidate is read from the workspace and compared whole-file.

## Trusting a failure: the baseline gate

Before a `java_build` failure is attributed to an agent, the identical command,
JDK, locale and unprivileged user must build an **unmodified checkout** green.
Without this, harness defects are recorded as model failures. This gate caught:

* an unset locale gave the JVM an ASCII default charset, failing suites that
  compare accented text;
* the agent ran as `root` while the build ran as `runner`, leaving undeletable
  scratch files;
* a `-Djava.io.tmpdir` override of ours broke `FilesUncheckTest`;
* 93 rows of the SWE-Refactor dataset ship a truncated build command,
  `-Dtest='!A,!B` with no closing quote, which dies in `/bin/sh` before Maven
  starts.

The last is repaired at ingest, and a command the shell cannot parse fails with
`malformed_build_command` rather than being blamed on the model.

## Adding a metric

Three things: a directory, a manifest, one function.

```yaml
# plugins/evaluation/changed_lines/plugin.yaml
type: evaluation
key: changed_lines
name: Lines added
entrypoint: plugin:Plugin
```

```python
# plugins/evaluation/changed_lines/plugin.py
from app.catalog.sdk import EvalContext, EvaluationPlugin, MetricOption, MetricSpec, StageResult


class Plugin(EvaluationPlugin):
    key = "changed_lines"
    reason = "too_few_lines_changed"

    spec = MetricSpec(
        title="Lines added",
        summary="Counts added lines in the captured diff and compares them against a minimum.",
        requires="nothing beyond the captured diff",
        outputs=("addedLines",),
        options=(MetricOption(key="minimum", label="Minimum added lines", type="integer", default=1),),
    )

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        added = sum(1 for line in ctx.diff_text.splitlines()
                    if line.startswith("+") and not line.startswith("+++"))
        ok = added >= int(config.get("minimum", 1))
        return StageResult(ok=ok, reason="" if ok else self.reason,
                           message=f"{added} line(s) added", outputs={"addedLines": added})
```

Any benchmark can then reference it:

```yaml
verify:
  - {preset: changed_lines, config: {minimum: 3}}
```

Check it before running anything:

```bash
make plugin PLUGIN=plugins/evaluation/changed_lines
```

`spec` is what the dashboard reads: without a title and a summary the plugin does
not load, because a stage an operator cannot interpret is worse than no stage.
`requires` is stated where the metric is listed; `gates=False` marks a metric
that only records, and a benchmark that puts one among its gates is refused.
`availability()` reports a missing library or tool without a task, so it appears
on the Plugins screen rather than inside a failed run. A copyable version of the
above is in [`examples/plugins/evaluation/example_metric/`](../examples/plugins/evaluation/example_metric).

`ctx` carries the task, the workspace, the captured diff, the agent's session,
the benchmark's data directory, and `ctx.shared` for values a benchmark's prepare
step published. `ctx.reference("params.test_file")` resolves an option that points
at a task field instead of holding a literal, which is how one metric serves
benchmarks whose fields differ.

## Rules the code enforces

* A stage's structured `outputs` flow into the result. Nothing re-parses its own
  English message.
* The platform records a stage under the metric's id, so evidence and the
  pipeline that produced it cannot disagree.
* Test counts are read only from a runner's own summary line. Maven prints
  `[INFO] 14 errors` on a *compile* failure; that is not fourteen tests.
* Cost is computed from the provider's published per-token prices. A model with
  no published price yields no cost, and a negative rate (OpenRouter's `-1`
  sentinel for "depends which model the router picks") is not a price.
* The agent reports output tokens per message but prompt tokens and true context
  occupancy only at `session.shutdown`. Mid-run the dashboard shows what was
  measured and marks the rest as not yet reported. It does not extrapolate.
* Finished runs and imported archives keep the stage names they recorded. Stored
  evidence is never rewritten.

## Benchmark correctness versus setup conformance

The benchmark verdict and the execution-regime evidence are separate facts. A
task may pass its tests while the agent ignores the mechanism that was meant to
distinguish the setup. Every task therefore exports `setupCompliance` alongside
`passed` and `reason`:

| Value | Meaning |
|---|---|
| `conformant` | The requested setup was provided and its required mechanism was observed. For `s1`, no setup-only mechanism was observed. |
| `setup_not_exercised` | The setup was available, but no required LSP, self-check, or native sub-agent action was observed. |
| `unexpected_capability_use` | A mechanism excluded from the selected setup appeared in the event evidence, contaminating the comparison. |
| `setup_unavailable` | The platform could not provide the requested capability; the task is an infrastructure error, never a fallback S1 result. |

`s1_lsp` additionally requires a successful JSON-RPC `initialize` handshake before
the agent launches. `s1_eval` stores each bounded self-check under
`eval/self-checks/attempt-NNNN/` with its stage results and logs; missing run,
task, workspace, or plugin state fails closed. If the first S1-eval pass omits the
mandatory check and the CLI supports exact-session resume, the platform continues
that session once within the original timeout; it does not change the benchmark
verdict or create an unbounded retry loop. `s3` is conformant only when the agent
event stream contains a native `task` invocation. S2 is conformant after mandatory
context pre-injection; optional retrieval-tool calls remain a separate count.

Benchmark pass or fail is independent of setup non-conformance. Comparing setups
requires both columns: correctness says the edit worked, conformance says the
claimed intervention occurred.
