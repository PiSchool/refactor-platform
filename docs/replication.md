# Replication

The acceptance suite includes **12 single-task end-to-end
runs**, each benchmark (RefactorBench, SWE-Refactor) across S1, S1-LSP,
S1-eval, S3, S2-naive, and S2-AST, on the composed Docker stack with real BYOK
credentials.

The completed 21 July 2026 campaign, including exact accepted run IDs and
excluded attempts, is recorded in
[Setup conformance results](setup-conformance-results.md).

## Prerequisites

- Docker + Docker Compose.
- An OpenRouter API key. For this no-credit conformance campaign, every row runs
  through OpenRouter BYOK with `openrouter/free`; this is a test choice, not a
  platform model restriction.

## 1. Configure

```bash
cp .env.example .env
# set OPENROUTER_API_KEY=...
# keep OPENROUTER_MODEL=openrouter/free for this campaign
```

## 2. Build + start

```bash
docker compose up --build -d
docker compose logs -f backend      # wait for "Application startup complete"
```

## 3. Bootstrap benchmark data (once)

```bash
docker compose exec backend python -m app.catalog.bootstrap
# refbench: clones RefactorBench repositories
# swe:      downloads the Zenodo release (task JSONs + RefactoringMiner) + Java mirrors
```

Both report `ready`. Data lands in named volumes (`refbench-data`, `swe-data`)
so it survives restarts. Benchmark source data is not fetched at task time. The
first S2 task waits for the model server to hold the embedding and
query-expansion models, and downloads the reranker into its persistent cache;
later S2 tasks reuse both. Record the models a campaign ran with, from
[Retrieval (S2)](retrieval.md#models): results produced with different models are
not comparable.

## 4. Run the matrix

Open http://localhost:3000 → **New run**. For each of the 8 combinations pick
the benchmark, **one** task, `copilot` + `openrouter/free`, and the setup:

| # | Benchmark | Setup |
|---|---|---|
| 1 | RefactorBench | s1 |
| 2 | RefactorBench | s1_lsp |
| 3 | RefactorBench | s1_eval |
| 4 | RefactorBench | s3 |
| 5 | SWE-Refactor | s1 |
| 6 | SWE-Refactor | s1_lsp |
| 7 | SWE-Refactor | s1_eval |
| 8 | SWE-Refactor | s3 |

Runs are sequential; launch them and they queue.

Paid models must not be substituted for failed rows. Provider/rate-limit
failures remain failed observations and must be retried later with
`openrouter/free`.

### Retrieval (S2) acceptance extension

The eight-row matrix above reproduces the reported non-retrieval acceptance
suite. The released Retrieval (S2) implementation is validated with four
additional single-task runs, using the same task per benchmark for both
strategies:

| # | Benchmark | Setup |
|---|---|---|
| 9 | RefactorBench | s2_rag_naive |
| 10 | RefactorBench | s2_rag_ast |
| 11 | SWE-Refactor | s2_rag_naive |
| 12 | SWE-Refactor | s2_rag_ast |

S2 task verification includes:

- the **Retrieval** tab contains pre-injected snippets and opens queries, ranked
  hits, provenance, and tool-call evidence;
- `retrievalPreInjected=true` and `setupExercised=true` in the result/export;
  `retrievalIndexKey` ties a result to the exact index it was produced against;
- naive and AST runs have different `indexKey` values;
- the second identical run reports `cacheHit=true` in `provenance.json`;
- missing pgvector/model access produces `retrieval_unavailable` and does not
  launch a plain S1 agent.

For all twelve rows, `setupCompliance=conformant` is required in the
exported run CSV. A benchmark `passed=true` value is not evidence
that the setup was exercised. For `s1_lsp`, require `lspActions > 0`; for
`s1_eval`, require `evalAttempts > 0` and inspect the retained self-check result;
for `s3`, require `subagentInvocations > 0`. Baseline `s1` must have zero LSP,
evaluation-tool, retrieval-tool, and sub-agent actions.

Retrieval (S2) outcomes are not merged into historical study
percentages. The released model stack differs; see [retrieval.md](retrieval.md).

## 5. What to verify per run

The run detail view has **Agent**, **Repository**, **Output**, **Prompt**, and
**Events** tabs; S2 runs additionally have **Retrieval**.

- **Live**: the Agent tab streams the agent's own PTY. Toggle *Steps* for a
  grouped, GitHub-Actions-style log, or *Terminal* for the raw bytes.
  Status flips queued → running → completed.
- **Replay**: reload the run after completion: the terminal replays the exact
  same bytes from `terminal.log`; nothing is reconstructed.
- **Repository**: the exact checkout the agent works in. *Changes* renders the
  diff (files → hunks → lines); *All files* is a navigable tree of the whole
  repo with changed files badged. Both update **while the agent is running**:
  the diff is recomputed from the working tree through a throwaway git index,
  so the agent's own index is never touched.
- **Output**: the raw build/test output per evaluation stage (`python_tests`,
  `java_build`, `refactoring_miner`): the evidence behind the verdict.
- **Checks** (Results column): the benchmark's verify pipeline, shown as
  pending from the moment the run starts and filled in as stages complete.
  Test stages report counts, e.g. `python_tests: 4/5 tests passed.`
  The footer shows where the wall-clock went: agent time vs evaluation time.
- **Result**: a pass/fail with a machine reason. A *failure* here is a valid
  outcome: the agent's edit didn't pass the benchmark's real tests / AST
  check, not that the platform misbehaved. See "Verifying a failure is real".
- **Export**: `Export ZIP` yields `summary.json` + `results.csv` + artifacts;
  `CSV` exports one run, `/api/runs.csv` exports every task of every run.

Browsing a *finished* task's repository requires `Keep task workspaces`
(Settings → General, on by default). Turning it off reclaims disk (a guava
checkout is hundreds of MB) at the cost of post-hoc navigation.

## Notes on outcomes

Pass/fail depends on the model. With a weak/free model, agent edits often fail
the real RefactorBench pytest suite or the SWE-Refactor RefactoringMiner+build
gate, correctly classified (`test_failed`, `compile_test_failed`,
`ast_verification_failed`). The platform claim under test is **reproducible
execution and evaluation**, not agent success rate.

### The baseline gate

Before trusting any `java_build` verdict, confirm the **unmodified** checkout
builds green in the container. If a clean tree fails, the harness, not the
agent, is at fault:

```bash
docker compose exec backend bash -lc '
  MIR=/data/mirrors/$(python3 -c "import hashlib;print(hashlib.sha1(b\"https://github.com/apache/commons-io.git\").hexdigest())").git
  rm -rf /tmp/bl && mkdir -p /tmp/bl && git -C $MIR archive <before-sha> | tar -x -C /tmp/bl
  chown -R runner:runner /tmp/bl /tmp/rp-m2
  su runner -c "cd /tmp/bl && mvn clean package -Drat.skip=true -Dmaven.javadoc.skip=true -Dmaven.repo.local=/tmp/rp-m2"'
# → BUILD SUCCESS (the exact test count depends on the pinned task revision)
```

Three environment faults were found and fixed this way (each made a *clean*
checkout fail, blaming the agent):

| Fault | Symptom on an unmodified tree |
|---|---|
| Build ran as `root` | root bypasses `chmod`; permission-denial tests (`testCanRead`, `testThrowsOnCannotDeleteFile`) fail |
| No locale set | Java default charset `ANSI_X3.4-1968`; accented-text assertions fail |
| `env` never passed to `subprocess.run` | per-task `JAVA_HOME` had no effect; JDK selection was inert |
| Agent ran as `root`, build as `runner` | the agent shells out to `mvn`, leaving root-owned scratch in `/tmp` that the build cannot delete → phantom `Cannot delete file` errors |

The agent session and the evaluation build now share **one** unprivileged
identity (`runner`, see `app/execution/sandbox.py`) with `LANG=C.UTF-8`.
`java.io.tmpdir` is **not** overridden: `FilesUncheckTest` asserts
on its value.

### Verifying a failure is real, not a harness bug

Every gating stage writes a log under the task's `eval/` directory
(`java_build.log`, `refactoring_miner.log`, …), so a failure can always be
traced to its cause. The evaluation toolchain has explicit controls:

```bash
# RefactoringMiner: positive + negative control
RM=plugins/benchmarks/swe/data/data/tools/RefactoringMiner-3.0.10/bin/RefactoringMiner
$RM -scr src/A.java before.java after.java "Extract Method"   # → "true true"
$RM -scr src/A.java before.java before.java "Extract Method"  # → "false false"
```

Worked example from the acceptance suite (SWE-Refactor / commons-io, S1): the
agent edited the target file, but introduced `Files.readString(Path, Charset)`
(a Java 11+ API) into a module whose pom pins `maven.compiler.release=8`.
Maven rejected it (`compile_test_failed`) and RefactoringMiner
reported no Extract Method (`false false`). Both verdicts are the
agent's fault, not the harness's: the JDK selection, Maven run, and detector
all behaved as intended.

The dataset's `compileJDK` is the JDK that *runs* Maven; a project's
own pom (`maven.compiler.release`) governs the language level it compiles to.

## Toolchain baked into the backend image

`temurin-{8,11,17,21}-jdk` (per-task JDK selection with a 21→17 fallback),
Maven, Gradle, Node 24, the six agent CLIs, `pylsp`, `jdtls`, and the
RefactoringMiner binary shipped in the SWE-Refactor plugin data.

## Acceptance matrix

Eight runs: two benchmarks × four setups, one task each, live provider
(`openrouter/free`, GitHub Copilot CLI). Reproduce with the New-Run wizard or:

```bash
BENCH=$(curl -s localhost:8000/api/catalog | jq -r '.benchmarks[]|select(.key=="swe").id')
AGENT=$(curl -s localhost:8000/api/catalog | jq -r '.agents[0].id')
for S in s1 s1_lsp s1_eval s3; do
  curl -s -X POST localhost:8000/api/runs -H 'Content-Type: application/json' -d "{
    \"benchmarkId\":\"$BENCH\", \"setupId\":\"$S\", \"agentToolId\":\"$AGENT\",
    \"model\":\"openrouter/free\", \"taskTimeoutSeconds\":7200,
    \"taskKeys\":[\"commons-io/010299c21811b11a41c8d5bd73023f75eb29058e_47_67_59_79_48_57\"]}"
done
```

Runs are queued and execute one at a time.

| Benchmark | Setup | Passed | Agent | Eval | Decisive check |
|---|---|---|---|---|---|
| RefactorBench | S1 | ✗ | 268 s | <1 s | `workspace_changed`: no changes were made |
| RefactorBench | S1-LSP | ✓ | 474 s | <1 s | `python_tests`: 5/5 |
| RefactorBench | S1-eval | ✓ | 401 s | <1 s | `python_tests`: 5/5 |
| RefactorBench | S3 | ✗ | 1161 s | <1 s | `python_tests`: 3/5 |
| SWE-Refactor | S1 | ✗ | 275 s | 75 s | `java_build`: compilation failed; no tests ran |
| SWE-Refactor | S1-LSP | ✓ | 939 s | 239 s | `java_build`: 2032/2032 |
| SWE-Refactor | S1-eval | ✓ | 381 s | 201 s | `java_build`: 2032/2032 |
| SWE-Refactor | S3 | ✓ | 749 s | 185 s | `java_build`: 2032/2032 |

Verdicts vary between runs: `openrouter/free` routes to whichever free model is
available, and free models are rate-limited. A run that ends `provider_error`
with `workspace_changed=false` means the agent never got to work, not that it
failed the task. The evaluation reports that distinctly.

### Baseline verification

A SWE-Refactor verdict is valid only when the baseline gate is green:

```bash
git clone https://github.com/apache/commons-io.git /tmp/baseline && cd /tmp/baseline
git checkout 3ca55e92e8493429317554ff220e71bf0125cf7f
setpriv --reuid=runner --regid=runner --init-groups env \
  HOME=/home/runner JAVA_HOME=$JDK_17_HOME LANG=C.UTF-8 LC_ALL=C.UTF-8 \
  mvn clean package -Drat.skip=true -Dmaven.javadoc.skip=true \
      -Dtest='!FileUtilsDeleteDirectoryLinuxTestCase,!ObservableInputStreamTest'
# expect: BUILD SUCCESS · Tests run: 2032, Failures: 0, Errors: 0, Skipped: 15
```

If that is not green, every "the agent broke the build" verdict is noise.
