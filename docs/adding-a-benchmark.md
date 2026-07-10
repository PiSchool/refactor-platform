# Adding a benchmark

A benchmark is a directory under `plugins/benchmarks/<key>/`. The minimum is a
`plugin.yaml` and a `tasks.yaml`. Python hooks are optional — a YAML-only
benchmark works if the core presets cover its evaluation.

The core never learns your benchmark's name. You compose it from the platform's
generic capabilities: workspace providers, capture stages, verify stages, and a
pass expression.

## 1. `plugin.yaml`

```yaml
type: benchmark
key: mybench                 # unique; also the plugins/ dir name
name: My Benchmark
version: 1.0.0
language: python             # default task language
setups: [s1, s1_lsp, s1_eval, s3]   # which setups this benchmark supports
prompt:
  template: prompts/task.md.j2       # optional Jinja2 template over the task
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

**Core presets** you can reference by name: `git_diff`, `events_metrics`,
`file_artifact`, `workspace_changed`, `python_tests`, `java_build`,
`refactoring_miner`. A name containing a `.` (e.g. `mybench.my_stage`) resolves
to a stage your Python hook returns from `stages()`.

`config` values support `params.x` (from the task's `params`) and `shared.x`
(written by an earlier stage into `EvalContext.shared`).

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
`generate_tasks.py` — commit `tasks.yaml`, gitignore the heavy data.

## 3. `data_bootstrap.py` (optional)

```python
def bootstrap(data_dir: Path) -> None:
    # download/clone/unpack into data_dir. Runs once; platform writes a
    # `.ready` sentinel on success, `.error` on failure. No network at task time.
```

Provisioning happens ahead of runs — either in the background at startup or via
`python -m app.catalog.bootstrap <key>`.

## 4. Custom stages (optional)

Subclass `BenchmarkPlugin` in `plugin.py` (entrypoint `plugin:Plugin`) when a
core preset isn't enough. A stage is a `StageFn = (EvalContext, config) -> StageResult`.

```python
from app.catalog.sdk import BenchmarkPlugin, EvalContext, StageResult, StageFn

class Plugin(BenchmarkPlugin):
    key = "mybench"
    def stages(self) -> dict[str, StageFn]:
        return {"my_stage": self._my_stage}
    def _my_stage(self, ctx: EvalContext, cfg: dict) -> StageResult:
        # inspect ctx.workspace / ctx.diff_text / ctx.session; write to ctx.shared
        return StageResult(name="mybench.my_stage", ok=True)
```

You may also override `build_prompt(task, ctx)` and `evaluate(ctx)` for full
control. Return `None` to fall back to templates/pipeline.

## 5. Verify

```bash
python -m app.catalog.bootstrap mybench     # data ready
uv run pytest tests/                        # SDK-boundary + loader tests still green
```

The benchmark appears in the New-Run wizard once its data state is `ready`. See
`plugins/benchmarks/refbench` (pure YAML + presets) and
`plugins/benchmarks/swe` (custom stages + shared-state handoff) as references.
