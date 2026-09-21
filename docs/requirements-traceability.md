# Requirements traceability

Locked specification decisions map to the code and tests that
deliver them, with stated omissions.

Status vocabulary:

| Status | Meaning |
|---|---|
| Done | Implemented and covered by an automated test named below |
| Partial | Implemented in part; the shortfall is stated in the same row |
| Superseded | Deliberately replaced later; the replacement is named in the same row |

Re-verify everything with:

```bash
cd server && uv run pytest                 # backend
cd web && npm test && npm run test:e2e     # dashboard unit + browser
docker compose config --quiet              # deployment topology
```

## Locked decisions

| # | Decision | Status | Code | Test |
|---|---|---|---|---|
| 1 | FastAPI + Uvicorn, async | Done | `server/app/main.py` | `tests/test_api.py` |
| 2 | PostgreSQL is the source of truth | Done | `docker-compose.yml`, `server/app/db/engine.py` | `tests/test_migrations.py::test_postgres_migrates_to_head_with_jsonb` |
| 3 | Multi-file specification set | Done | predecessor repository `docs/srs/` | - |
| 4 | In-process worker, no `state.json`, append-only blobs | Done | `server/app/execution/worker.py`, `execution/taskloop.py` | `tests/test_queue.py`, `tests/test_taskloop.py` |
| 5 | Directory + manifest plugin discovery at startup | Done | `server/app/catalog/loader.py`, `catalog/manifest.py` | `tests/test_catalog.py::test_invalid_manifest_is_skipped` |
| 6 | S3 uses the agent CLI's native sub-agent tool | Done | `server/app/execution/setups.py`, `plugins/agents/copilot` | `tests/test_setup_conformance.py::test_setup_execution_conformance_matrix` |
| 7 | Durable queued rows + asyncio signal, boot drain, sequential | Done | `server/app/execution/worker.py` | `tests/test_queue.py::test_enqueue_starts_and_second_queues`, `::test_boot_drain_picks_up_queued` |
| 8 | Strict per-run/per-task artifact tree with DB pointers | Done | `server/app/results/artifacts.py` | `tests/test_artifacts.py` |
| 9 | Per-task isolation from a cached bare mirror at a pinned ref | Done | `server/app/execution/workspace.py` | `tests/test_taskloop.py` |
| 10 | Toolchain bundled in the backend image, no Docker-in-Docker | Done | `docker/backend.Dockerfile` | `tests/test_setup_conformance.py::test_jdtls_adapter_selects_bundled_java_21` |
| 11 | Three services: frontend, backend, postgres | Done | `docker-compose.yml` | `tests/test_production_release.py::test_base_frontend_has_a_healthcheck` |
| 12 | No authentication | Delivered | one deployment, unauthenticated, both host mappings on loopback by default: `docker-compose.yml` | `tests/test_production_release.py` |
| 13 | One benchmark + setup + agent + model per run | Done | `server/app/api/schemas.py`, `api/runs.py` | `tests/test_api.py` |
| 14 | Always continue, record the outcome | Done | `server/app/execution/taskloop.py` | `tests/test_taskloop.py` |
| 15 | Completion on process exit + per-task wall clock | Done | `server/app/execution/pty_host.py`, `plugins/agents/copilot/events.py` | `tests/test_taskloop.py`, `tests/test_copilot_plugin.py` |
| 16 | Authoritative capture: diff + events, prompt/transcript persisted, tokens in DB | Done | `plugins/evaluation/git_diff/plugin.py`, `plugins/evaluation/events_metrics/plugin.py` | `tests/test_evaluation.py`, `tests/test_artifacts.py` |
| 17 | Agent-driven eval tool with counted iterations | Done | `server/app/execution/evaltool.py` | `tests/test_setup_conformance.py::test_self_check_attempts_are_capped_and_each_result_is_durable` |
| 18 | Java and Python language servers ship | Done | `plugins/lsp/jdtls`, `plugins/lsp/pylsp`, `server/app/execution/lsp.py` | `tests/test_setup_conformance.py::test_lsp_probe_performs_initialize_handshake` |
| 19 | Restart clones into a fresh run | Done | `server/app/execution/worker.py` | `tests/test_queue.py::test_restart_clones_into_new_queued` |
| 20 | Stop kills the session, skips the rest, finalizes `stopped` | Done | `server/app/execution/worker.py`, `execution/taskloop.py` | `tests/test_queue.py::test_stop_kills_the_active_task_and_skips_the_remainder`, `::test_stop_finalizes_a_queued_run_without_ever_executing_it` |
| 21 | Read-only catalog and health, editable runtime config, env-only secrets | Done | `server/app/api/settings.py`, `api/system.py`, `db/runtime.py` | `tests/test_api.py` |
| 22 | Universal metrics + per-benchmark extras | Done | `server/app/db/models.py` | `tests/test_models.py` |
| 23 | Task subset selection + one run-level timeout | Done | `server/app/api/schemas.py`, `web/components/run-wizard.tsx` | `tests/test_api.py`, `web/e2e/operator-flow.spec.ts` |
| 24 | Per-run ZIP export | Done | `server/app/results/export.py`, `results/bundle.py` | `tests/test_bundle.py`, `web/e2e/operator-flow.spec.ts` |
| 25 | Rows kept forever, blobs pruned by cap, delete removes both | Done | `server/app/results/retention.py`, `api/runs.py` | `tests/test_retention.py`, `tests/test_queue.py::test_delete_refuses_an_active_run_and_then_removes_rows_and_blobs` |
| 26 | Declarative task/repo data files + mirror cache | Done | `plugins/benchmarks/*/tasks.yaml`, `server/app/catalog/bootstrap.py` | `tests/test_refbench_plugin.py`, `tests/test_swe_plugin.py` |
| 27 | Plugin-owned evaluation over shared helpers | Done | `server/app/evaluation/engine.py`, `catalog/sdk.py` | `tests/test_evaluation.py` |
| 28 | Layered configuration: env, file, runtime overrides | Done | `server/app/config.py`, `config.yaml`, `server/app/db/runtime.py` | `tests/test_api.py`, `tests/test_production_release.py` |
| 29 | Modular monolith organized by domain | Done | `server/app/{api,catalog,execution,evaluation,results,realtime,retrieval}` | `tests/test_catalog.py::test_plugin_import_boundary` |
| 30 | Live terminal over a multiplexer attach | Superseded | platform-owned PTY + WebSocket: `server/app/execution/pty_host.py`, `realtime/ws_terminal.py` | `tests/test_realtime.py::test_terminal_replay_to_live_handoff_has_no_duplicate_or_lost_bytes` |
| 31 | Transcript captured at session end | Superseded | continuous append with byte-offset replay/resume | `tests/test_realtime.py::test_terminal_completed_replay_honors_resume_offset` |
| 32 | WebSocket for bytes, server-sent events for status | Done | `server/app/realtime/sse.py`, `realtime/ws_terminal.py` | `tests/test_realtime.py::test_run_sse_emits_status` |
| 33 | Same frontend stack and design | Done | `web/package.json`, `web/app`, `web/components` | `web` unit suite, `web/e2e/operator-flow.spec.ts` |
| 34 | Fully normalized run → task → result + session | Done | `server/app/db/models.py` | `tests/test_models.py`, `tests/test_migrations.py` |
| 35 | Plugin task files upserted into a task table | Done | `server/app/catalog/sync.py` | `tests/test_catalog.py` |
| 36 | S3 modelled exactly like S1 | Done | `server/app/execution/setups.py` | `tests/test_setup_conformance.py` |
| 37 | Platform-owned task loop; plugins own prompt, evaluation, launch | Done | `server/app/execution/taskloop.py`, `catalog/sdk.py` | `tests/test_taskloop.py`, `tests/test_catalog.py::test_plugin_import_boundary` |
| 38 | Composable metrics, no bespoke bundled tooling | Done | `plugins/evaluation/` (one directory per metric), `server/app/evaluation/registry.py` | `tests/test_evaluation.py`, `tests/test_extensibility.py` |
| 39 | Hybrid composition: declarative pipeline + optional override | Done | `plugins/benchmarks/refbench/plugin.yaml` (declarative), `plugins/benchmarks/swe` (custom stages) | `tests/test_refbench_plugin.py`, `tests/test_swe_plugin.py` |
| 40 | Four capture presets | Partial | `presets/git_diff.py`, `presets/events_metrics.py`, `presets/file_artifact.py`; transcript capture is unconditional in `execution/pty_host.py` rather than an opt-in preset | `tests/test_evaluation.py`, `tests/test_realtime.py` |
| 41 | Four verification presets plus a validator | Done | `presets/refactoring_miner.py`, `presets/java_build.py`, `presets/python_tests.py`, `presets/workspace_changed.py`, `presets/file_artifact.py`, and Python structural diff in `plugins/evaluation/pyrefactor` | `tests/test_evaluation.py`, `tests/test_pyrefactor_plugin.py::test_preset_fails_when_the_expected_refactoring_is_absent` |
| 42 | Benchmark facets in task parameters, generically filtered | Done | `plugins/benchmarks/*/plugin.yaml`, `server/app/api/catalog.py`, `web/components/run-wizard.tsx` | `tests/test_catalog.py` |

## Departures from the specification

| Original decision | What ships instead | Why |
|---|---|---|
| Terminal multiplexer attach and end-of-session capture | Platform-owned PTY, continuous log append, byte-offset replay and resume | The multiplexer was the source of the lost-scrollback and live-versus-archive split defects; owning the PTY removes both and makes replay byte-exact |
| No retrieval, no S2 | Mandatory always-on retrieval with pgvector, in a selectable model profile | Retrieval-backed setups became a product requirement; making it fail-closed prevents degraded comparisons |
| No authentication | One unauthenticated deployment on loopback; reaching it from another machine is an SSH tunnel or a reverse proxy providing TLS and authentication | A second authenticated read-only mode was built and removed: two deployment paths doubled what had to be tested and documented, for one temporary need |
| Archive format versions and legacy import | One strict manifest contract; anything else is rejected | Nothing is deployed yet, so compatibility layers would be permanent cost for no benefit |
| Retention prunes the oldest runs | Imported archives are exempt and do not consume the cap | Archive evidence cannot be reproduced locally, so age must never delete it |
| Python structural diff as a bundled verification preset | The metric `pyrefactor`, one directory under `plugins/evaluation/`, usable from any benchmark's `verify` list and its `passed` expression | Every measurement is an add-on directory, including the ones that ship: one contract, one place to look, and the shipped metrics exercise the same path a third party's does |

## Quality gates

| Gate | Evidence |
|---|---|
| Migrations apply from empty | `tests/test_migrations.py::test_fresh_database_is_upgraded_to_alembic_head` |
| Plugins auto-discovered | `tests/test_catalog.py` |
| Run enqueues and starts immediately | `tests/test_queue.py::test_enqueue_starts_and_second_queues` |
| Live terminal streams and replays without loss | `tests/test_realtime.py` |
| Results persist and export as a ZIP | `tests/test_bundle.py`, `web/e2e/operator-flow.spec.ts` |
| Retention prunes blobs and keeps rows | `tests/test_retention.py` |
| Dashboard operator journey works in a browser | `web/e2e/operator-flow.spec.ts` |
| Java tasks start from a green baseline | `tests/test_java_baseline.py` |
| Every shipped agent CLI is installed in the backend image | `tests/test_production_release.py::test_every_shipped_agent_cli_is_installed_in_the_backend_image` |
| Two installed plugins may ship a module of the same name | `tests/test_extensibility.py::test_two_plugins_may_ship_a_module_of_the_same_name`, `::test_two_benchmarks_may_ship_a_provisioning_helper_of_the_same_name` |
| Every shipped adapter parses a session through the real registry | `tests/test_extensibility.py::test_every_shipped_adapter_parses_a_session_into_the_contract_type` |
| One task's failure never ends the run, and no row is left open | `tests/test_taskloop.py::test_a_result_that_cannot_be_recorded_fails_only_its_own_task`, `tests/test_queue.py::test_a_crash_outside_the_task_boundary_closes_the_whole_run`, `::test_startup_closes_tasks_stranded_under_a_finished_run` |

## Not delivered

- **Authoring-time verification that a task's reference commit is a genuine
  refactoring.** Recorded in the specification as a future extension point; see
  `docs/adding-a-benchmark.md`.
- **Multi-user accounts, roles, or single sign-on.** The operator stack is
  single-user by design; sharing results is an exported archive, not an account.
- **Parallel execution.** Runs and tasks remain strictly sequential, as specified.
