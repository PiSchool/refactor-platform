# Adding a benchmark

One of several extension points; [Extending](extending.md) is the overview.

A benchmark is a directory under `plugins/benchmarks/<key>/`. The minimum is a
`plugin.yaml` and a `tasks.yaml`. Python hooks are optional; a YAML-only
benchmark works if the core presets cover its evaluation.

The core never learns your benchmark's name. You compose it from the platform's
generic capabilities: workspace providers, capture stages, verify stages, and a
pass expression.

## 1. `plugin.yaml`

```yaml
type: benchmark
key: mybench                 # unique; also the plugins/ dir name
name: My Benchmark
language: python             # default task language
setups: [s1, s1_lsp, s1_eval, s3]   # which setups this benchmark supports
prompt:
  template: prompts/task.md          # optional template over the task
  appliesTo: every task in this benchmark    # shown beside the template
  pathsRelativeTo: params.cwd_hint   # optional; see 5. Prompt templates
  variables:                                # what the template must keep
    - {name: task.instructions, summary: What the agent must do.}
    - {name: params.test_file, summary: The suite the verdict runs., required: false}
data:
  bootstrap: data_bootstrap.py       # optional; omit if no external data
evaluation:
  capture: [git_diff, events_metrics]   # non-gating artifact stages
  verify:                                # gating stages, in order
    - {preset: workspace_changed}
    - preset: python_tests
      config: {runner: runpy, test_from: params.test_file, timeout: 300}
  passed: "workspace_changed and python_tests"   # bool expr over stage names
```

Every name is a metric installed under `plugins/evaluation/`, referenced by its
directory name: `workspace_changed`, `git_diff`, `events_metrics`,
`file_artifact`, `python_tests`, `pytest_suite`, `java_build`,
`refactoring_miner`, `pyrefactor`, `codebleu`. Your benchmark configures them; it
does not define one; a measurement of your own is [its own
directory](evaluation.md#adding-a-metric), where every other benchmark can use it
too.

`config` values support `params.x` (from the task's `params`) and `shared.x`
(published by your `prepare` hook into `EvalContext.shared`). Declare that hook
as `evaluation.prepare: <name>` and implement `prepare(ctx)` plus
`describe_preparation()`; it runs once before the metrics and is recorded as the
pipeline's first step.

## 2. `tasks.yaml`

```yaml
tasks:
  - task_key: project/case#variant     # unique within the benchmark
    title: Human-readable title
    language: python
    workspace:
      type: snapshot                    # or: git
      source: repositories/project      # snapshot: path under data dir
      # git: source is a repo URL, plus `ref: <sha>`
    instructions: What the agent must do.
    params: {test_file: tests/...py, cwd_hint: lib}   # free-form, used by stages
```

Generate this file from your raw dataset in `data_bootstrap.py` /
`generate_tasks.py`; commit `tasks.yaml`, gitignore the heavy data.

## 3. `data_bootstrap.py` (optional)

```python
def bootstrap(data_dir: Path) -> None:
    # download/clone/unpack into data_dir. Runs once; platform writes a
    # `.ready` sentinel on success, `.error` on failure. No network at task time.
```

Provisioning happens ahead of runs: either in the background at startup or via
`cd server && uv run python -m app.catalog.bootstrap <key>` for a local
development checkout. In Docker, use
`docker compose exec backend python -m app.catalog.bootstrap <key>`.

## 4. Python hooks (optional)

Subclass `BenchmarkPlugin` in `plugin.py` (entrypoint `plugin:Plugin`) when YAML
is not enough. Three hooks exist, each returning `None` to keep the default:

```python
from app.catalog.sdk import BenchmarkPlugin, EvalContext, MetricSpec, StageResult

class Plugin(BenchmarkPlugin):
    key = "mybench"

    def build_prompt(self, task, ctx) -> str | None:
        ...                                  # instead of the manifest's template

    def prepare(self, ctx: EvalContext) -> StageResult | None:
        ctx.shared["reference_text"] = ...   # what the metrics read
        return StageResult(ok=True, message="Prepared the candidate.")

    def describe_preparation(self) -> MetricSpec | None:
        return MetricSpec(title="Prepare", summary="What it puts in place.")

    def evaluate(self, ctx: EvalContext) -> EvalOutcome | None:
        ...                                  # instead of the manifest's pipeline
```

A benchmark cannot define a metric: the loader refuses one that tries, and names
`plugins/evaluation/` instead. `prepare` is the hook for work that is not a
measurement, and it must be declared as `evaluation.prepare` in the manifest.

## 5. Prompt templates

The template in `plugin.yaml` is rendered with Jinja over `task` and `params`.
List in `prompt.variables` the values it must keep: **Settings → Prompts** then
marks each one present or missing in the text being edited and refuses to save an
edit that drops a required one. Declare nothing and the platform can only report
that the template is rendered over `task` and `params`.

`pathsRelativeTo` names the task field holding the directory the task's own
instructions write their paths relative to, when that is not the repository root.
RefactorBench's dataset asks for `requests/utils.py` in a checkout that keeps
that file at `src/requests/utils.py`; declaring `params.cwd_hint` puts one line in
the prompt resolving the difference, with an example taken from the task, instead
of each agent discovering it by reading paths that do not exist.

A plugin that builds its prompt itself chooses the template per task and
substitutes values into it, and only the plugin knows which:

```python
    def describe_prompts(self) -> dict[str, PromptSpec]:
        return {"extract.txt": PromptSpec(          # the file name, not its path
            applies_to="tasks whose refactoring type is Extract Method",
            syntax="format",                    # `{name}`; use "jinja" for `{{ name }}`
            variables=(
                PromptVariable("code_to_refactor", "the method as it stands"),
                PromptVariable("project_structure", "the package tree", required=False),
            ),
        )}
```

Keyed by file name, or `"*"` for every template the benchmark ships, and takes
precedence over the manifest's declaration. A template without
`code_to_refactor` reaches the agent with no code in it, which is what the
refusal prevents.

## 6. Verify

```bash
cd server
uv run python -m app.catalog.bootstrap mybench  # data ready
uv run pytest                                   # SDK-boundary + loader tests still green
```

The benchmark appears in the New-Run wizard once its data state is `ready`. See
`plugins/benchmarks/refbench` (pure YAML + presets),
`plugins/benchmarks/pyrefactor-live` (pure YAML, tasks pinned to commits in
public repositories, verdict from two plugin metrics) and
`plugins/benchmarks/swe` (custom stages + shared-state handoff) as references.

`pyrefactor-live` is the shortest complete example: four tasks over `toolz` and
`more-itertools`, each requiring one named refactoring, each verified twice: the
structural check that the change *is* that refactoring, and the project's own
suite to show it survived. Its bootstrap reads the clone URLs and pinned commits
out of `tasks.yaml`, so adding a task is the only step needed to add a project.

## Task quality is the author's responsibility

The platform verifies what an *agent* produced; it does not verify what a task
*claims*. Authoring-time checking that a task's reference ("gold") commit really
is a behaviour-preserving refactoring is a deliberate future extension point and
is not implemented. Validate reference commits before declaring a task file
`ready`; an unsound task silently becomes an unsound benchmark result.

For `pyrefactor-live` this was done by hand: each of the four tasks was solved,
the detector was checked to name the requested refactoring, and the project's
test target was run on the result. Two candidate targets were dropped at that
stage because the transformation could not be applied without changing
behaviour.
