# Appendix: Complete Per-Task Results (All Runs)

---

### Run 1: qwen3.6-flash S1 descriptive RefactorBench
Source: `refbench-qwen3.6-flash-full.csv` | Rows: 104 | Columns: 14
  Run ID,benchmark_pipeline_20260509_045651 | Status,completed | Model,qwen/qwen3.6-flash | Datasets,refbench

| # | Task | Status | Input | Output | Cache | Time | Reqs | +Lines | -Lines | Files | Apply | Test | Result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | add-log-parameter-get-group-vars | completed | 202.0k | 2.6k | - | 27s | - | 3 | 2 | 2 | yes | yes | PASSED |
| 2 | add-log-parameter-is-systemd-managed | completed | 257.4k | 3.9k | - | 32s | - | 4 | 3 | 3 | yes | yes | PASSED |
| 3 | combine-namespace-compat | completed | 516.8k | 5.1k | - | 53s | - | 32 | 8 | 6 | yes | no | FAILED |
| 4 | data-to-inventory-data | completed | 318.8k | 4.4k | - | 39s | - | 2 | 2 | 2 | yes | yes | PASSED |
| 5 | move-quoting-splitter | completed | 1.3M | 13.1k | - | 1m59s | - | 17 | 7 | 7 | yes | yes | PASSED |
| 6 | new-inventory-patterns | completed | 247.7k | 4.5k | - | 34s | - | 103 | 75 | 3 | yes | yes | PASSED |
| 7 | new-utils-class-connection | completed | 513.2k | 7.7k | - | 1m04s | - | 53 | 51 | 3 | yes | yes | PASSED |
| 8 | new-utils-from-basic | completed | 2.0M | 22.8k | - | 2m47s | - | 153 | 137 | 13 | yes | no | FAILED |
| 9 | parse_key_value | completed | 384.2k | 6.2k | - | 50s | - | 33 | 33 | 12 | yes | yes | PASSED |
| 10 | rename-lenient-lowercase | completed | 274.8k | 3.4k | - | 30s | - | 9 | 9 | 3 | yes | yes | PASSED |
| 11 | sort-groups-to-group-sort | completed | 163.5k | 2.9k | - | 22s | - | 4 | 4 | 2 | yes | yes | PASSED |
| 12 | add-log-parameter-get-digest-algorithm | completed | 144.1k | 1.5k | - | 16s | - | 2 | 2 | 2 | yes | yes | PASSED |
| 13 | add-log-parameter-node-format | completed | 186.2k | 3.3k | - | 25s | - | 5 | 5 | 3 | yes | yes | PASSED |
| 14 | annotation-utils | completed | 202.1k | 3.4k | - | 26s | - | 11 | 5 | 3 | yes | no | FAILED |
| 15 | autoretry-to-retry | completed | 681.0k | 8.7k | - | 1m17s | - | 81 | 69 | 6 | yes | yes | PASSED |
| 16 | combine-unpickle-task | completed | 169.9k | 2.7k | - | 21s | - | 6 | 10 | 3 | yes | no | FAILED |
| 17 | dump-message-to-serialization | completed | 177.0k | 2.2k | - | 20s | - | 9 | 8 | 2 | yes | yes | PASSED |
| 18 | ensure_serialize | completed | 220.5k | 3.2k | - | 28s | - | 9 | 9 | 4 | yes | yes | PASSED |
| 19 | evaluate-promises-to-serialization | completed | 290.7k | 4.5k | - | 41s | - | 9 | 8 | 2 | yes | yes | PASSED |
| 20 | expand-router-string-to-utils | completed | 225.3k | 1.9k | - | 22s | - | 10 | 9 | 2 | yes | yes | PASSED |
| 21 | object-mro-lookup | completed | 125.1k | 1.2k | - | 12s | - | 2 | 1 | 1 | yes | yes | PASSED |
| 22 | rename-host-format | completed | 151.8k | 2.4k | - | 19s | - | 10 | 10 | 4 | yes | yes | PASSED |
| 23 | truncate-text | completed | 265.6k | 5.2k | - | 44s | - | 17 | 17 | 7 | yes | yes | PASSED |
| 24 | add-log-parameter-constant-time-compare | completed | 244.1k | 5.3k | - | 40s | - | 15 | 14 | 7 | yes | no | FAILED |
| 25 | add-log-parameter-get-resolver | completed | 1.5M | 14.9k | - | 2m23s | - | 34 | 29 | 11 | yes | no | FAILED |
| 26 | add-log-parameter-resolve-error-handler | completed | 824.8k | 9.7k | - | 1m29s | - | 13 | 8 | 4 | yes | no | FAILED |
| 27 | add-none-handling-duration-string | completed | 172.8k | 1.7k | - | 18s | - | 5 | - | 2 | yes | no | FAILED |
| 28 | combine-utils-dates-dateformat | completed | 235.6k | 4.1k | - | 31s | - | 78 | 10 | 3 | yes | yes | PASSED |
| 29 | combine-utils-hashable-itercompat | completed | 199.1k | 5.7k | - | 35s | - | 111 | 13 | 14 | yes | yes | PASSED |
| 30 | new-converter-to-python-class | completed | 394.8k | 4.1k | - | 48s | - | 53 | - | 3 | yes | yes | PASSED |
| 31 | new-path-traversal-exception | completed | 1.5M | 16.5k | - | 2m13s | - | 15 | 8 | 5 | yes | no | FAILED |
| 32 | new-reference-context-field-class | completed | 518.4k | 5.9k | - | 58s | - | 34 | 18 | 3 | yes | yes | PASSED |
| 33 | new-reference-context-graph-class | completed | 2.0M | 15.4k | - | 3m11s | - | 51 | 54 | 4 | yes | yes | PASSED |
| 34 | new-timezone-class | completed | 692.3k | 8.5k | - | 1m17s | - | 8 | 8 | 2 | yes | no | FAILED |
| 35 | new-utils-adapt-method-mode | completed | 427.8k | 4.1k | - | 44s | - | 38 | 37 | 2 | yes | yes | PASSED |
| 36 | new-utils-check-response | completed | 364.8k | 4.9k | - | 44s | - | 35 | 30 | 2 | yes | yes | PASSED |
| 37 | new-utils-path-from-module | completed | 327.8k | 4.3k | - | 39s | - | 38 | 31 | 2 | yes | yes | PASSED |
| 38 | remove-core-cache-utils | completed | 290.4k | 3.9k | - | 36s | - | 17 | 5 | 4 | yes | yes | PASSED |
| 39 | remove-db-models-constants | completed | 253.9k | 5.8k | - | 38s | - | 34 | 20 | 20 | yes | yes | PASSED |
| 40 | rename-file-move-safe | completed | 264.9k | 5.3k | - | 48s | - | 20 | 20 | 5 | yes | yes | PASSED |
| 41 | split-parse-apps-and-model-labels | completed | 369.0k | 3.2k | - | 37s | - | 31 | 22 | 3 | yes | yes | PASSED |
| 42 | add-log-parameter-generate-option-id-for-path | completed | 101.7k | 1.3k | - | 13s | - | 2 | 2 | 2 | yes | yes | PASSED |
| 43 | exception-handlers-to-handlers | completed | 316.7k | 4.4k | - | 38s | - | 9 | 9 | 9 | yes | yes | PASSED |
| 44 | get-auth-scheme-param | completed | 369.8k | 4.8k | - | 42s | - | 9 | 9 | 3 | yes | yes | PASSED |
| 45 | openapi-get-utils | completed | 374.6k | 6.8k | - | 53s | - | 7 | 7 | 7 | yes | no | FAILED |
| 46 | params-to-param | completed | 970.0k | 12.3k | - | 1m51s | - | 5 | 5 | 2 | yes | yes | PASSED |
| 47 | value-is-a-sequence | completed | 134.6k | 1.3k | - | 15s | - | 3 | 3 | 2 | yes | yes | PASSED |
| 48 | add-log-parameter-get-debug-flag | completed | 332.3k | 5.0k | - | 40s | - | 8 | 5 | 4 | yes | yes | PASSED |
| 49 | add-log-parameter-get-flashed-messages | completed | 188.5k | 2.7k | - | 26s | - | 9 | 7 | 2 | yes | yes | PASSED |
| 50 | debughelpers-to-helpers.py | completed | 188.5k | 2.7k | - | 26s | - | 9 | 7 | 2 | no | no | TIMEOUT |
| 51 | rename-send-from-directory | completed | 342.4k | 7.6k | - | 55s | - | 11 | 8 | 5 | yes | yes | PASSED |
| 52 | render-template-str | completed | 145.3k | 4.1k | - | 25s | - | 14 | 14 | 8 | yes | yes | PASSED |
| 53 | stream-template-str | completed | 112.0k | 1.1k | - | 13s | - | 2 | 2 | 2 | yes | yes | PASSED |
| 54 | add-log-parameter-get-encoding-from-headers | completed | 152.0k | 2.1k | - | 20s | - | 3 | 3 | 3 | yes | yes | PASSED |
| 55 | add-log-parameter-resolve-proxies | completed | 123.2k | 1.5k | - | 14s | - | 3 | 3 | 2 | yes | yes | PASSED |
| 56 | add-log-parameter-select-proxy | completed | 127.8k | 2.4k | - | 20s | - | 5 | 4 | 2 | yes | yes | PASSED |
| 57 | combine-from-key-to-key | completed | 201.2k | 4.6k | - | 31s | - | 20 | 39 | 3 | yes | no | FAILED |
| 58 | combine-internal-utils-utils | completed | 616.8k | 9.3k | - | 1m23s | - | 50 | 15 | 6 | yes | yes | PASSED |
| 59 | move-hooks-sessions | completed | 294.4k | 4.3k | - | 41s | - | 24 | 6 | 4 | yes | no | FAILED |
| 60 | new-cookie-utils-class | completed | 2.1M | 22.2k | - | 3m04s | - | 273 | 203 | 7 | yes | yes | PASSED |
| 61 | rename-lookup-dict-dict-lookup | completed | 95.1k | 1.9k | - | 13s | - | 7 | 7 | 3 | yes | yes | PASSED |
| 62 | rename-super-len-complex-len | completed | 190.1k | 4.1k | - | 28s | - | 28 | 28 | 3 | yes | yes | PASSED |
| 63 | split-warnings-exceptions | completed | 210.1k | 3.4k | - | 30s | - | 24 | 19 | 4 | yes | yes | PASSED |
| 64 | add-log-parameter-delete-directory | completed | 166.7k | 2.4k | - | 22s | - | 2 | 2 | 2 | yes | yes | PASSED |
| 65 | add-log-parameter-get-capability-definitions | completed | 199.5k | 4.1k | - | 29s | - | 11 | 8 | 3 | yes | yes | PASSED |
| 66 | add-log-parameter-recursive-diff | completed | 742.4k | 9.7k | - | 1m30s | - | 9 | 4 | 2 | yes | yes | PASSED |
| 67 | cant-create | completed | 148.6k | 1.8k | - | 16s | - | 4 | 4 | 3 | yes | yes | PASSED |
| 68 | channel-to-transport | completed | 235.6k | 3.4k | - | 29s | - | 3 | 3 | 2 | yes | yes | PASSED |
| 69 | ex-pillar-fail | completed | 121.4k | 1.4k | - | 14s | - | 1 | 1 | 1 | yes | yes | PASSED |
| 70 | ex-state-fail | completed | 120.4k | 1.6k | - | 17s | - | 4 | 4 | 3 | yes | yes | PASSED |
| 71 | exactly-n-boto-mod | completed | 433.4k | 6.9k | - | 56s | - | 7 | 19 | 2 | yes | no | FAILED |
| 72 | get-unavail | completed | 121.4k | 1.5k | - | 16s | - | 4 | 4 | 4 | yes | yes | PASSED |
| 73 | iam-to-aws | completed | 235.0k | 2.4k | - | 28s | - | 41 | 1 | 1 | yes | yes | PASSED |
| 74 | mksls-to-specific | completed | 118.8k | 1.5k | - | 15s | - | 3 | 3 | 3 | yes | yes | PASSED |
| 75 | namecheap-xmlutil | completed | 313.7k | 3.9k | - | 35s | - | 101 | 73 | 2 | yes | yes | PASSED |
| 76 | paged-call-boto-mod | completed | 126.3k | 1.7k | - | 20s | - | 1 | 15 | 1 | yes | no | FAILED |
| 77 | pem-fingerprint | completed | 925.6k | 12.1k | - | 1m52s | - | 25 | 25 | 12 | yes | yes | PASSED |
| 78 | perm-denied | completed | 165.4k | 1.6k | - | 21s | - | 2 | 2 | 2 | yes | yes | PASSED |
| 79 | add-log-parameter-disconnect-all | completed | 117.9k | 1.8k | - | 16s | - | 3 | 3 | 3 | yes | yes | PASSED |
| 80 | add-log-parameter-job-dir | completed | 184.2k | 2.4k | - | 23s | - | 5 | 4 | 4 | yes | no | FAILED |
| 81 | add-log-parameter-xmliter | completed | 512.4k | 15.9k | - | 1m55s | - | 19 | 16 | 2 | yes | no | FAILED |
| 82 | genspider-functions-to-utils-url | completed | 213.6k | 3.4k | - | 26s | - | 30 | 30 | 2 | yes | yes | PASSED |
| 83 | new-downloadermiddlewares-utils | completed | 168.6k | 2.9k | - | 24s | - | 26 | 20 | 2 | yes | no | FAILED |
| 84 | new-spider-utils-in-spiders | completed | 553.4k | 6.1k | - | 1m01s | - | 75 | 43 | 3 | yes | no | FAILED |
| 85 | new-verify-reactor-class | completed | 1.3M | 10.1k | - | 2m17s | - | 62 | 44 | 6 | yes | no | FAILED |
| 86 | not-supported-exception-to-unsupported | completed | 207.0k | 3.9k | - | 30s | - | 16 | 16 | 6 | yes | yes | PASSED |
| 87 | parameterize-gunzip | completed | 990.4k | 10.0k | - | 1m49s | - | 33 | 26 | 5 | yes | no | FAILED |
| 88 | rename-description-commands | completed | 336.8k | 5.6k | - | 50s | - | 23 | 23 | 15 | yes | no | FAILED |
| 89 | rename-engine-status | completed | 635.9k | 4.0k | - | 1m08s | - | 16 | 16 | 6 | yes | yes | PASSED |
| 90 | rename-processtest-testproc | completed | 228.6k | 2.6k | - | 26s | - | 9 | 9 | 5 | yes | yes | PASSED |
| 91 | sitemap-url-to-url | completed | 668.6k | 6.8k | - | 1m12s | - | 24 | 16 | 4 | yes | yes | PASSED |
| 92 | global-objects | completed | 255.9k | 6.2k | - | 42s | - | 38 | 28 | 4 | yes | no | FAILED |
| 93 | log-utils | completed | 378.6k | 5.5k | - | 48s | - | 154 | 130 | 4 | yes | yes | PASSED |
| 94 | option-parser-with-pretty-print | completed | 1.2M | 25.8k | - | 3m22s | - | 66 | 52 | 2 | yes | no | FAILED |
| 95 | options-utils | completed | 2.7M | 31.0k | - | 6m00s | - | 410 | 186 | 25 | yes | no | FAILED |
| 96 | remove-locale-data | completed | 592.9k | 9.3k | - | 1m20s | - | 1 | 1 | 1 | yes | yes | PASSED |
| 97 | rename-http1connection | completed | 211.2k | 5.0k | - | 34s | - | 13 | 13 | 5 | yes | yes | PASSED |
| 98 | rename-to-camel-case | completed | 214.1k | 4.6k | - | 37s | - | 10 | 10 | 4 | yes | yes | PASSED |
| 99 | resolvers-as-separate | completed | 1.9M | 18.0k | - | 2m26s | - | 324 | 302 | 11 | yes | no | FAILED |
| 100 | tcpclient-connect-params | completed | 1.2M | 14.7k | - | 2m07s | - | 94 | 18 | 5 | yes | yes | PASSED |
| Summary |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Failed | 26 |  |  |  |  |  |  |  |  |  |  |  |  |
| Timed out | 1 |  |  |  |  |  |  |  |  |  |  |  |  |
| Success rate | 73% |  |  |  |  |  |  |  |  |  |  |  |  |

---

### Run 2: qwen3.6-flash S2-naive all modes RefactorBench
Source: `s2_rag_naive_qwen36flash_all_modes_refbench.csv` | Rows: 300 | Columns: 17

| # | mode | repo | task_id | status | duration_s | tests_passed | tests_total |
|---|---|---|---|---|---|---|---|
| 1 | base | ansible_refactor | add-log-parameter-get-group-vars | success | 37.58 | 5 | 5 |
| 2 | base | ansible_refactor | add-log-parameter-is-systemd-managed | success | 67.08 | 5 | 5 |
| 3 | base | ansible_refactor | combine-namespace-compat | failed | 85.37 | 6 | 7 |
| 4 | base | ansible_refactor | data-to-inventory-data | success | 50.79 | 5 | 5 |
| 5 | base | ansible_refactor | move-quoting-splitter | failed | 60.85 | 1 | 6 |
| 6 | base | ansible_refactor | new-inventory-patterns | success | 97.27 | 9 | 9 |
| 7 | base | ansible_refactor | new-utils-class-connection | timed_out | 81.12 |  | 7 |
| 8 | base | ansible_refactor | new-utils-from-basic | failed | 198.77 |  | 12 |
| 9 | base | ansible_refactor | parse_key_value | success | 81.46 | 21 | 21 |
| 10 | base | ansible_refactor | rename-lenient-lowercase | success | 44.41 | 4 | 4 |
| 11 | base | ansible_refactor | sort-groups-to-group-sort | success | 40.61 | 4 | 4 |
| 12 | base | celery_refactor | add-log-parameter-get-digest-algorithm | success | 39.79 | 5 | 5 |
| 13 | base | celery_refactor | add-log-parameter-node-format | success | 50.1 | 3 | 3 |
| 14 | base | celery_refactor | annotation-utils | failed | 58.06 | 5 | 8 |
| 15 | base | celery_refactor | autoretry-to-retry | failed | 92.47 | 6 | 7 |
| 16 | base | celery_refactor | combine-unpickle-task | failed | 54.06 | 5 | 6 |
| 17 | base | celery_refactor | dump-message-to-serialization | success | 118.89 | 3 | 3 |
| 18 | base | celery_refactor | ensure_serialize | success | 94.75 | 9 | 9 |
| 19 | base | celery_refactor | evaluate-promises-to-serialization | success | 54.1 | 4 | 4 |
| 20 | base | celery_refactor | expand-router-string-to-utils | failed | 68.33 | 3 | 4 |
| 21 | base | celery_refactor | object-mro-lookup | success | 52.04 | 3 | 3 |
| 22 | base | celery_refactor | rename-host-format | failed | 78.47 | 6 | 7 |
| 23 | base | celery_refactor | truncate-text | failed | 226.85 |  | 9 |
| 24 | base | django_refactor | add-log-parameter-constant-time-compare | failed | 98.91 | 2 | 3 |
| 25 | base | django_refactor | add-log-parameter-get-resolver | failed | 183.83 | 2 | 3 |
| 26 | base | django_refactor | add-log-parameter-resolve-error-handler | failed | 68.3 |  | 2 |
| 27 | base | django_refactor | add-none-handling-duration-string | success | 66.13 | 3 | 3 |
| 28 | base | django_refactor | combine-utils-dates-dateformat | success | 68.23 | 4 | 4 |
| 29 | base | django_refactor | combine-utils-hashable-itercompat | failed | 216.52 | 3 | 4 |
| 30 | base | django_refactor | new-converter-to-python-class | failed | 50.26 | 1 | 3 |
| 31 | base | django_refactor | new-path-traversal-exception | failed | 147.5 | 7 | 9 |
| 32 | base | django_refactor | new-reference-context-field-class | timed_out | 54.46 |  | 4 |
| 33 | base | django_refactor | new-reference-context-graph-class | failed | 204.55 | 5 | 9 |
| 34 | base | django_refactor | new-timezone-class | timed_out | 184.11 |  | 4 |
| 35 | base | django_refactor | new-utils-adapt-method-mode | success | 82.44 | 3 | 3 |
| 36 | base | django_refactor | new-utils-check-response | success | 60.11 | 2 | 2 |
| 37 | base | django_refactor | new-utils-path-from-module | success | 82.24 | 2 | 2 |
| 38 | base | django_refactor | remove-core-cache-utils | failed | 58.27 | 4 | 5 |
| 39 | base | django_refactor | remove-db-models-constants | success | 444.07 | 19 | 19 |
| 40 | base | django_refactor | rename-file-move-safe | success | 131.93 | 6 | 6 |
| 41 | base | django_refactor | split-parse-apps-and-model-labels | failed | 52.09 | 2 | 5 |
| 42 | base | fastapi_refactor | add-log-parameter-generate-option-id-for-path | success | 62.36 | 5 | 5 |
| 43 | base | fastapi_refactor | exception-handlers-to-handlers | failed | 119.33 | 11 | 12 |
| 44 | base | fastapi_refactor | get-auth-scheme-param | success | 58.38 | 6 | 6 |
| 45 | base | fastapi_refactor | openapi-get-utils | success | 68.57 | 9 | 9 |
| 46 | base | fastapi_refactor | params-to-param | failed | 80.45 | 10 | 22 |
| 47 | base | fastapi_refactor | value-is-a-sequence | success | 33.89 | 5 | 5 |
| 48 | base | flask_refactor | add-log-parameter-get-debug-flag | success | 49.93 | 7 | 7 |
| 49 | base | flask_refactor | add-log-parameter-get-flashed-messages | success | 70.22 | 3 | 3 |
| 50 | base | flask_refactor | debughelpers-to-helpers.py | timed_out | 15.36 |  | 5 |
| 51 | base | flask_refactor | rename-send-from-directory | timed_out | 63.13 | 1 | 4 |
| 52 | base | flask_refactor | render-template-str | success | 74.38 | 10 | 10 |
| 53 | base | flask_refactor | stream-template-str | failed | 37.62 | 3 | 4 |
| 54 | base | requests_refactor | add-log-parameter-get-encoding-from-headers | failed | 47.8 | 2 | 3 |
| 55 | base | requests_refactor | add-log-parameter-resolve-proxies | success | 62.04 | 2 | 2 |
| 56 | base | requests_refactor | add-log-parameter-select-proxy | timed_out | 45.88 |  | 2 |
| 57 | base | requests_refactor | combine-from-key-to-key | success | 84.28 | 5 | 5 |
| 58 | base | requests_refactor | combine-internal-utils-utils | failed | 214.26 | 1 | 7 |
| 59 | base | requests_refactor | move-hooks-sessions | failed | 472.27 | 4 | 7 |
| 60 | base | requests_refactor | new-cookie-utils-class | failed | 259.88 |  | 4 |
| 61 | base | requests_refactor | rename-lookup-dict-dict-lookup | success | 51.92 | 7 | 7 |
| 62 | base | requests_refactor | rename-super-len-complex-len | failed | 68.15 | 2 | 3 |
| 63 | base | requests_refactor | split-warnings-exceptions | success | 86.35 | 9 | 9 |
| 64 | base | salt_refactor | add-log-parameter-delete-directory | success | 47.97 | 4 | 4 |
| 65 | base | salt_refactor | add-log-parameter-get-capability-definitions | success | 112.41 | 3 | 3 |
| 66 | base | salt_refactor | add-log-parameter-recursive-diff | success | 121.55 | 6 | 6 |
| 67 | base | salt_refactor | cant-create | failed | 48.69 | 6 | 8 |
| 68 | base | salt_refactor | channel-to-transport | failed | 59.14 | 3 | 6 |
| 69 | base | salt_refactor | ex-pillar-fail | success | 48.33 | 5 | 5 |
| 70 | base | salt_refactor | ex-state-fail | failed | 45.12 | 5 | 6 |
| 71 | base | salt_refactor | exactly-n-boto-mod | failed | 123.61 | 2 | 4 |
| 72 | base | salt_refactor | get-unavail | success | 43.57 | 10 | 10 |
| 73 | base | salt_refactor | iam-to-aws | success | 61.48 | 5 | 5 |
| 74 | base | salt_refactor | mksls-to-specific | success | 59.12 | 6 | 6 |
| 75 | base | salt_refactor | namecheap-xmlutil | success | 121.54 | 6 | 6 |
| 76 | base | salt_refactor | paged-call-boto-mod | failed | 72.86 | 1 | 4 |
| 77 | base | salt_refactor | pem-fingerprint | success | 73.24 | 10 | 10 |
| 78 | base | salt_refactor | perm-denied | failed | 42.3 | 4 | 5 |
| 79 | base | scrapy_refactor | add-log-parameter-disconnect-all | success | 48.22 | 6 | 6 |
| 80 | base | scrapy_refactor | add-log-parameter-job-dir | failed | 46.22 | 3 | 5 |
| 81 | base | scrapy_refactor | add-log-parameter-xmliter | failed | 232.92 | 2 | 3 |
| 82 | base | scrapy_refactor | genspider-functions-to-utils-url | failed | 72.48 |  | 4 |
| 83 | base | scrapy_refactor | new-downloadermiddlewares-utils | success | 54.16 | 5 | 5 |
| 84 | base | scrapy_refactor | new-spider-utils-in-spiders | timed_out | 842.16 | 3 | 8 |
| 85 | base | scrapy_refactor | new-verify-reactor-class | failed | 126.36 | 8 | 11 |
| 86 | base | scrapy_refactor | not-supported-exception-to-unsupported | failed | 62.53 | 8 | 10 |
| 87 | base | scrapy_refactor | parameterize-gunzip | timed_out | 56.17 | 1 | 9 |
| 88 | base | scrapy_refactor | rename-description-commands | success | 66.69 | 7 | 7 |
| 89 | base | scrapy_refactor | rename-engine-status | success | 70.55 | 8 | 8 |
| 90 | base | scrapy_refactor | rename-processtest-testproc | failed | 60.42 |  | 6 |
| 91 | base | scrapy_refactor | sitemap-url-to-url | failed | 58.34 | 1 | 3 |
| 92 | base | tornado_refactor | global-objects | failed | 225.07 |  |  |
| 93 | base | tornado_refactor | log-utils | failed | 151.85 |  |  |
| 94 | base | tornado_refactor | option-parser-with-pretty-print | failed | 188.19 |  |  |
| 95 | base | tornado_refactor | options-utils | failed | 204.68 |  |  |
| 96 | base | tornado_refactor | remove-locale-data | failed | 84.59 |  |  |
| 97 | base | tornado_refactor | rename-http1connection | timed_out | 32.2 |  |  |
| 98 | base | tornado_refactor | rename-to-camel-case | failed | 72.75 |  |  |
| 99 | base | tornado_refactor | resolvers-as-separate | timed_out | 194.35 |  |  |
| 100 | base | tornado_refactor | tcpclient-connect-params | failed | 226.76 |  |  |
| 101 | lazy | ansible_refactor | add-log-parameter-get-group-vars | failed | 49.87 | 3 | 5 |
| 102 | lazy | ansible_refactor | add-log-parameter-is-systemd-managed | timed_out | 40.45 | 2 | 5 |
| 103 | lazy | ansible_refactor | combine-namespace-compat | success | 192.85 | 7 | 7 |
| 104 | lazy | ansible_refactor | data-to-inventory-data | failed | 69.19 | 4 | 5 |
| 105 | lazy | ansible_refactor | move-quoting-splitter | failed | 144.23 | 5 | 6 |
| 106 | lazy | ansible_refactor | new-inventory-patterns | failed | 124.04 | 8 | 9 |
| 107 | lazy | ansible_refactor | new-utils-class-connection | success | 213.13 | 7 | 7 |
| 108 | lazy | ansible_refactor | new-utils-from-basic | failed | 131.8 | 1 | 12 |
| 109 | lazy | ansible_refactor | parse_key_value | success | 134.19 | 21 | 21 |
| 110 | lazy | ansible_refactor | rename-lenient-lowercase | success | 105.72 | 4 | 4 |
| 111 | lazy | ansible_refactor | sort-groups-to-group-sort | success | 46.45 | 4 | 4 |
| 112 | lazy | celery_refactor | add-log-parameter-get-digest-algorithm | success | 50.18 | 5 | 5 |
| 113 | lazy | celery_refactor | add-log-parameter-node-format | failed | 119.09 | 2 | 3 |
| 114 | lazy | celery_refactor | annotation-utils | failed | 93.62 | 3 | 8 |
| 115 | lazy | celery_refactor | autoretry-to-retry | timed_out | 43.93 |  | 7 |
| 116 | lazy | celery_refactor | combine-unpickle-task | failed | 54.18 | 4 | 6 |
| 117 | lazy | celery_refactor | dump-message-to-serialization | timed_out | 48.02 |  | 3 |
| 118 | lazy | celery_refactor | ensure_serialize | failed | 64.37 | 2 | 9 |
| 119 | lazy | celery_refactor | evaluate-promises-to-serialization | success | 105.08 | 4 | 4 |
| 120 | lazy | celery_refactor | expand-router-string-to-utils | failed | 50.0 | 3 | 4 |
| 121 | lazy | celery_refactor | object-mro-lookup | success | 41.97 | 3 | 3 |
| 122 | lazy | celery_refactor | rename-host-format | success | 72.23 | 7 | 7 |
| 123 | lazy | celery_refactor | truncate-text | success | 101.06 | 9 | 9 |
| 124 | lazy | django_refactor | add-log-parameter-constant-time-compare | failed | 62.22 |  | 3 |
| 125 | lazy | django_refactor | add-log-parameter-get-resolver | failed | 110.83 |  | 3 |
| 126 | lazy | django_refactor | add-log-parameter-resolve-error-handler | failed | 101.06 | 1 | 2 |
| 127 | lazy | django_refactor | add-none-handling-duration-string | failed | 42.07 | 2 | 3 |
| 128 | lazy | django_refactor | combine-utils-dates-dateformat | failed | 117.51 | 1 | 4 |
| 129 | lazy | django_refactor | combine-utils-hashable-itercompat | failed | 74.44 |  | 4 |
| 130 | lazy | django_refactor | new-converter-to-python-class | failed | 238.27 |  | 3 |
| 131 | lazy | django_refactor | new-path-traversal-exception | failed | 183.53 | 5 | 9 |
| 132 | lazy | django_refactor | new-reference-context-field-class | failed | 182.41 | 2 | 4 |
| 133 | lazy | django_refactor | new-reference-context-graph-class | failed | 60.17 | 5 | 9 |
| 134 | lazy | django_refactor | new-timezone-class | success | 425.7 | 4 | 4 |
| 135 | lazy | django_refactor | new-utils-adapt-method-mode | success | 128.14 | 3 | 3 |
| 136 | lazy | django_refactor | new-utils-check-response | success | 70.25 | 2 | 2 |
| 137 | lazy | django_refactor | new-utils-path-from-module | failed | 92.64 |  | 2 |
| 138 | lazy | django_refactor | remove-core-cache-utils | failed | 161.69 |  | 5 |
| 139 | lazy | django_refactor | remove-db-models-constants | success | 200.3 | 19 | 19 |
| 140 | lazy | django_refactor | rename-file-move-safe | success | 128.95 | 6 | 6 |
| 141 | lazy | django_refactor | split-parse-apps-and-model-labels | failed | 79.13 | 1 | 5 |
| 142 | lazy | fastapi_refactor | add-log-parameter-generate-option-id-for-path | timed_out | 50.06 | 3 | 5 |
| 143 | lazy | fastapi_refactor | exception-handlers-to-handlers | failed | 186.24 | 11 | 12 |
| 144 | lazy | fastapi_refactor | get-auth-scheme-param | timed_out | 90.7 | 3 | 6 |
| 145 | lazy | fastapi_refactor | openapi-get-utils | success | 169.97 | 9 | 9 |
| 146 | lazy | fastapi_refactor | params-to-param | failed | 115.38 | 20 | 22 |
| 147 | lazy | fastapi_refactor | value-is-a-sequence | success | 54.44 | 5 | 5 |
| 148 | lazy | flask_refactor | add-log-parameter-get-debug-flag | failed | 222.52 | 3 | 7 |
| 149 | lazy | flask_refactor | add-log-parameter-get-flashed-messages | failed | 58.0 | 2 | 3 |
| 150 | lazy | flask_refactor | debughelpers-to-helpers.py | timed_out | 15.44 |  | 5 |
| 151 | lazy | flask_refactor | rename-send-from-directory | success | 174.15 | 4 | 4 |
| 152 | lazy | flask_refactor | render-template-str | timed_out | 27.62 | 1 | 10 |
| 153 | lazy | flask_refactor | stream-template-str | failed | 50.13 | 1 | 4 |
| 154 | lazy | requests_refactor | add-log-parameter-get-encoding-from-headers | failed | 216.2 | 1 | 3 |
| 155 | lazy | requests_refactor | add-log-parameter-resolve-proxies | success | 69.79 | 2 | 2 |
| 156 | lazy | requests_refactor | add-log-parameter-select-proxy | failed | 80.44 | 1 | 2 |
| 157 | lazy | requests_refactor | combine-from-key-to-key | failed | 80.45 | 1 | 5 |
| 158 | lazy | requests_refactor | combine-internal-utils-utils | failed | 110.75 | 5 | 7 |
| 159 | lazy | requests_refactor | move-hooks-sessions | timed_out | 62.02 | 1 | 7 |
| 160 | lazy | requests_refactor | new-cookie-utils-class | failed | 250.85 |  | 4 |
| 161 | lazy | requests_refactor | rename-lookup-dict-dict-lookup | success | 43.84 | 7 | 7 |
| 162 | lazy | requests_refactor | rename-super-len-complex-len | success | 88.45 | 3 | 3 |
| 163 | lazy | requests_refactor | split-warnings-exceptions | failed | 195.99 | 7 | 9 |
| 164 | lazy | salt_refactor | add-log-parameter-delete-directory | failed | 136.32 | 2 | 4 |
| 165 | lazy | salt_refactor | add-log-parameter-get-capability-definitions | success | 203.5 | 3 | 3 |
| 166 | lazy | salt_refactor | add-log-parameter-recursive-diff | failed | 362.72 | 3 | 6 |
| 167 | lazy | salt_refactor | cant-create | success | 48.55 | 8 | 8 |
| 168 | lazy | salt_refactor | channel-to-transport | success | 73.89 | 6 | 6 |
| 169 | lazy | salt_refactor | ex-pillar-fail | success | 60.01 | 5 | 5 |
| 170 | lazy | salt_refactor | ex-state-fail | success | 75.45 | 6 | 6 |
| 171 | lazy | salt_refactor | exactly-n-boto-mod | timed_out | 46.79 |  | 4 |
| 172 | lazy | salt_refactor | get-unavail | success | 47.77 | 10 | 10 |
| 173 | lazy | salt_refactor | iam-to-aws | success | 107.95 | 5 | 5 |
| 174 | lazy | salt_refactor | mksls-to-specific | failed | 64.36 | 5 | 6 |
| 175 | lazy | salt_refactor | namecheap-xmlutil | success | 160.06 | 6 | 6 |
| 176 | lazy | salt_refactor | paged-call-boto-mod | failed | 75.13 | 1 | 4 |
| 177 | lazy | salt_refactor | pem-fingerprint | success | 119.49 | 10 | 10 |
| 178 | lazy | salt_refactor | perm-denied | timed_out | 159.56 | 1 | 5 |
| 179 | lazy | scrapy_refactor | add-log-parameter-disconnect-all | failed | 80.52 | 2 | 6 |
| 180 | lazy | scrapy_refactor | add-log-parameter-job-dir | failed | 56.24 | 1 | 5 |
| 181 | lazy | scrapy_refactor | add-log-parameter-xmliter | failed | 76.4 | 2 | 3 |
| 182 | lazy | scrapy_refactor | genspider-functions-to-utils-url | failed | 84.75 |  | 4 |
| 183 | lazy | scrapy_refactor | new-downloadermiddlewares-utils | failed | 78.47 |  | 5 |
| 184 | lazy | scrapy_refactor | new-spider-utils-in-spiders | success | 145.48 | 8 | 8 |
| 185 | lazy | scrapy_refactor | new-verify-reactor-class | failed | 179.94 | 8 | 11 |
| 186 | lazy | scrapy_refactor | not-supported-exception-to-unsupported | failed | 45.99 | 5 | 10 |
| 187 | lazy | scrapy_refactor | parameterize-gunzip | failed | 210.43 | 3 | 9 |
| 188 | lazy | scrapy_refactor | rename-description-commands | failed | 62.54 | 5 | 7 |
| 189 | lazy | scrapy_refactor | rename-engine-status | failed | 102.97 | 7 | 8 |
| 190 | lazy | scrapy_refactor | rename-processtest-testproc | failed | 72.55 |  | 6 |
| 191 | lazy | scrapy_refactor | sitemap-url-to-url | failed | 68.39 | 2 | 3 |
| 192 | lazy | tornado_refactor | global-objects | failed | 107.02 |  |  |
| 193 | lazy | tornado_refactor | log-utils | failed | 190.26 |  |  |
| 194 | lazy | tornado_refactor | option-parser-with-pretty-print | failed | 164.09 |  |  |
| 195 | lazy | tornado_refactor | options-utils | timed_out | 200.74 |  |  |
| 196 | lazy | tornado_refactor | remove-locale-data | failed | 293.68 |  |  |
| 197 | lazy | tornado_refactor | rename-http1connection | failed | 86.69 |  |  |
| 198 | lazy | tornado_refactor | rename-to-camel-case | failed | 117.04 |  |  |
| 199 | lazy | tornado_refactor | resolvers-as-separate | failed | 153.46 |  |  |
| 200 | lazy | tornado_refactor | tcpclient-connect-params | failed | 76.5 |  |  |
| 201 | descriptive | ansible_refactor | add-log-parameter-get-group-vars | success | 80.92 | 5 | 5 |
| 202 | descriptive | ansible_refactor | add-log-parameter-is-systemd-managed | success | 77.21 | 5 | 5 |
| 203 | descriptive | ansible_refactor | combine-namespace-compat | success | 120.19 | 7 | 7 |
| 204 | descriptive | ansible_refactor | data-to-inventory-data | success | 56.91 | 5 | 5 |
| 205 | descriptive | ansible_refactor | move-quoting-splitter | success | 75.56 | 6 | 6 |
| 206 | descriptive | ansible_refactor | new-inventory-patterns | success | 215.43 | 9 | 9 |
| 207 | descriptive | ansible_refactor | new-utils-class-connection | failed | 114.12 | 6 | 7 |
| 208 | descriptive | ansible_refactor | new-utils-from-basic | failed | 105.84 |  | 12 |
| 209 | descriptive | ansible_refactor | parse_key_value | success | 113.83 | 21 | 21 |
| 210 | descriptive | ansible_refactor | rename-lenient-lowercase | success | 93.27 | 4 | 4 |
| 211 | descriptive | ansible_refactor | sort-groups-to-group-sort | timed_out | 52.7 |  | 4 |
| 212 | descriptive | celery_refactor | add-log-parameter-get-digest-algorithm | success | 46.25 | 5 | 5 |
| 213 | descriptive | celery_refactor | add-log-parameter-node-format | success | 64.35 | 3 | 3 |
| 214 | descriptive | celery_refactor | annotation-utils | failed | 169.12 | 7 | 8 |
| 215 | descriptive | celery_refactor | autoretry-to-retry | failed | 84.64 | 6 | 7 |
| 216 | descriptive | celery_refactor | combine-unpickle-task | failed | 62.43 | 5 | 6 |
| 217 | descriptive | celery_refactor | dump-message-to-serialization | success | 71.65 | 3 | 3 |
| 218 | descriptive | celery_refactor | ensure_serialize | success | 75.4 | 9 | 9 |
| 219 | descriptive | celery_refactor | evaluate-promises-to-serialization | success | 95.73 | 4 | 4 |
| 220 | descriptive | celery_refactor | expand-router-string-to-utils | failed | 71.36 | 3 | 4 |
| 221 | descriptive | celery_refactor | object-mro-lookup | success | 42.15 | 3 | 3 |
| 222 | descriptive | celery_refactor | rename-host-format | success | 74.45 | 7 | 7 |
| 223 | descriptive | celery_refactor | truncate-text | success | 167.94 | 9 | 9 |
| 224 | descriptive | django_refactor | add-log-parameter-constant-time-compare | success | 129.28 | 3 | 3 |
| 225 | descriptive | django_refactor | add-log-parameter-get-resolver | failed | 131.17 | 1 | 3 |
| 226 | descriptive | django_refactor | add-log-parameter-resolve-error-handler | failed | 83.65 |  | 2 |
| 227 | descriptive | django_refactor | add-none-handling-duration-string | failed | 79.47 | 2 | 3 |
| 228 | descriptive | django_refactor | combine-utils-dates-dateformat | timed_out | 58.31 |  | 4 |
| 229 | descriptive | django_refactor | combine-utils-hashable-itercompat | timed_out | 39.65 |  | 4 |
| 230 | descriptive | django_refactor | new-converter-to-python-class | success | 115.74 | 3 | 3 |
| 231 | descriptive | django_refactor | new-path-traversal-exception | failed | 87.61 | 7 | 9 |
| 232 | descriptive | django_refactor | new-reference-context-field-class | failed | 172.34 | 1 | 4 |
| 233 | descriptive | django_refactor | new-reference-context-graph-class | failed | 229.14 | 6 | 9 |
| 234 | descriptive | django_refactor | new-timezone-class | success | 106.71 | 4 | 4 |
| 235 | descriptive | django_refactor | new-utils-adapt-method-mode | failed | 122.19 | 2 | 3 |
| 236 | descriptive | django_refactor | new-utils-check-response | success | 80.96 | 2 | 2 |
| 237 | descriptive | django_refactor | new-utils-path-from-module | failed | 64.36 | 1 | 2 |
| 238 | descriptive | django_refactor | remove-core-cache-utils | success | 133.58 | 5 | 5 |
| 239 | descriptive | django_refactor | remove-db-models-constants | failed | 56.5 |  | 19 |
| 240 | descriptive | django_refactor | rename-file-move-safe | failed | 123.32 | 5 | 6 |
| 241 | descriptive | django_refactor | split-parse-apps-and-model-labels | success | 62.08 | 5 | 5 |
| 242 | descriptive | fastapi_refactor | add-log-parameter-generate-option-id-for-path | success | 67.49 | 5 | 5 |
| 243 | descriptive | fastapi_refactor | exception-handlers-to-handlers | success | 74.71 | 12 | 12 |
| 244 | descriptive | fastapi_refactor | get-auth-scheme-param | success | 89.97 | 6 | 6 |
| 245 | descriptive | fastapi_refactor | openapi-get-utils | failed | 90.83 | 8 | 9 |
| 246 | descriptive | fastapi_refactor | params-to-param | timed_out | 97.17 | 10 | 22 |
| 247 | descriptive | fastapi_refactor | value-is-a-sequence | success | 65.58 | 5 | 5 |
| 248 | descriptive | flask_refactor | add-log-parameter-get-debug-flag | success | 55.99 | 7 | 7 |
| 249 | descriptive | flask_refactor | add-log-parameter-get-flashed-messages | failed | 47.94 | 2 | 3 |
| 250 | descriptive | flask_refactor | debughelpers-to-helpers.py | timed_out | 15.53 |  | 5 |
| 251 | descriptive | flask_refactor | rename-send-from-directory | success | 122.18 | 4 | 4 |
| 252 | descriptive | flask_refactor | render-template-str | success | 95.32 | 10 | 10 |
| 253 | descriptive | flask_refactor | stream-template-str | success | 37.74 | 4 | 4 |
| 254 | descriptive | requests_refactor | add-log-parameter-get-encoding-from-headers | success | 51.88 | 3 | 3 |
| 255 | descriptive | requests_refactor | add-log-parameter-resolve-proxies | success | 60.01 | 2 | 2 |
| 256 | descriptive | requests_refactor | add-log-parameter-select-proxy | success | 41.85 | 2 | 2 |
| 257 | descriptive | requests_refactor | combine-from-key-to-key | success | 129.61 | 5 | 5 |
| 258 | descriptive | requests_refactor | combine-internal-utils-utils | success | 100.63 | 7 | 7 |
| 259 | descriptive | requests_refactor | move-hooks-sessions | failed | 102.56 | 3 | 7 |
| 260 | descriptive | requests_refactor | new-cookie-utils-class | success | 101.06 | 4 | 4 |
| 261 | descriptive | requests_refactor | rename-lookup-dict-dict-lookup | success | 39.68 | 7 | 7 |
| 262 | descriptive | requests_refactor | rename-super-len-complex-len | success | 89.09 | 3 | 3 |
| 263 | descriptive | requests_refactor | split-warnings-exceptions | success | 95.34 | 9 | 9 |
| 264 | descriptive | salt_refactor | add-log-parameter-delete-directory | success | 118.05 | 4 | 4 |
| 265 | descriptive | salt_refactor | add-log-parameter-get-capability-definitions | success | 50.71 | 3 | 3 |
| 266 | descriptive | salt_refactor | add-log-parameter-recursive-diff | success | 219.2 | 6 | 6 |
| 267 | descriptive | salt_refactor | cant-create | success | 57.0 | 8 | 8 |
| 268 | descriptive | salt_refactor | channel-to-transport | failed | 80.9 | 5 | 6 |
| 269 | descriptive | salt_refactor | ex-pillar-fail | failed | 61.2 | 4 | 5 |
| 270 | descriptive | salt_refactor | ex-state-fail | success | 58.57 | 6 | 6 |
| 271 | descriptive | salt_refactor | exactly-n-boto-mod | failed | 78.86 |  | 4 |
| 272 | descriptive | salt_refactor | get-unavail | success | 74.25 | 10 | 10 |
| 273 | descriptive | salt_refactor | iam-to-aws | success | 90.09 | 5 | 5 |
| 274 | descriptive | salt_refactor | mksls-to-specific | success | 52.48 | 6 | 6 |
| 275 | descriptive | salt_refactor | namecheap-xmlutil | success | 156.69 | 6 | 6 |
| 276 | descriptive | salt_refactor | paged-call-boto-mod | failed | 56.66 | 2 | 4 |
| 277 | descriptive | salt_refactor | pem-fingerprint | failed | 64.69 | 8 | 10 |
| 278 | descriptive | salt_refactor | perm-denied | failed | 48.32 | 4 | 5 |
| 279 | descriptive | scrapy_refactor | add-log-parameter-disconnect-all | success | 50.25 | 6 | 6 |
| 280 | descriptive | scrapy_refactor | add-log-parameter-job-dir | success | 73.51 | 5 | 5 |
| 281 | descriptive | scrapy_refactor | add-log-parameter-xmliter | success | 94.95 | 3 | 3 |
| 282 | descriptive | scrapy_refactor | genspider-functions-to-utils-url | success | 177.97 | 4 | 4 |
| 283 | descriptive | scrapy_refactor | new-downloadermiddlewares-utils | success | 66.32 | 5 | 5 |
| 284 | descriptive | scrapy_refactor | new-spider-utils-in-spiders | success | 160.22 | 8 | 8 |
| 285 | descriptive | scrapy_refactor | new-verify-reactor-class | failed | 119.27 | 8 | 11 |
| 286 | descriptive | scrapy_refactor | not-supported-exception-to-unsupported | success | 68.48 | 10 | 10 |
| 287 | descriptive | scrapy_refactor | parameterize-gunzip | failed | 111.06 | 5 | 9 |
| 288 | descriptive | scrapy_refactor | rename-description-commands | failed | 113.01 | 6 | 7 |
| 289 | descriptive | scrapy_refactor | rename-engine-status | success | 56.23 | 8 | 8 |
| 290 | descriptive | scrapy_refactor | rename-processtest-testproc | failed | 50.0 | 4 | 6 |
| 291 | descriptive | scrapy_refactor | sitemap-url-to-url | success | 93.14 | 3 | 3 |
| 292 | descriptive | tornado_refactor | global-objects | failed | 176.38 |  |  |
| 293 | descriptive | tornado_refactor | log-utils | failed | 196.75 |  |  |
| 294 | descriptive | tornado_refactor | option-parser-with-pretty-print | failed | 345.32 |  |  |
| 295 | descriptive | tornado_refactor | options-utils | timed_out | 1307.6 |  |  |
| 296 | descriptive | tornado_refactor | remove-locale-data | failed | 67.24 |  |  |
| 297 | descriptive | tornado_refactor | rename-http1connection | failed | 104.95 |  |  |
| 298 | descriptive | tornado_refactor | rename-to-camel-case | failed | 105.0 |  |  |
| 299 | descriptive | tornado_refactor | resolvers-as-separate | failed | 182.07 |  |  |
| 300 | descriptive | tornado_refactor | tcpclient-connect-params | failed | 92.61 |  |  |

---

### Run 3: qwen3.6-flash S2-naive desc
Source: `s2_rag_naive_descriptive_qwen36flash_refbench_detailed.csv` | Rows: 100 | Columns: 17

| # | task_id | repo | status | duration_s | input_tokens | output_tokens | cache_tokens | reasoning_tokens | requests | lines_added | lines_removed | files_modified | tests_passed | tests_total | timed_out | reason_short |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | add-log-parameter-get-group-vars | ansible_refactor | success | 37.58 | 106416 | 2018 | 0 | 656 | 6 | 4 | 3 | 3 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_add-log- |
| 2 | add-log-parameter-is-systemd-managed | ansible_refactor | success | 67.08 | 314203 | 4807 | 0 | 1101 | 16 | 4 | 3 | 3 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_add-log- |
| 3 | combine-namespace-compat | ansible_refactor | failed | 85.37 | 428663 | 7786 | 0 | 1726 | 17 | 32 | 54 | 7 | 6 | 7 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_combine- |
| 4 | data-to-inventory-data | ansible_refactor | success | 50.79 | 208320 | 2941 | 0 | 1110 | 11 | 2 | 2 | 2 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_data-to- |
| 5 | move-quoting-splitter | ansible_refactor | failed | 60.85 | 298885 | 4765 | 0 | 2693 | 15 | 13 | 10 | 2 | 1 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_move-quo |
| 6 | new-inventory-patterns | ansible_refactor | success | 97.27 | 637965 | 7239 | 0 | 2510 | 25 | 103 | 76 | 3 | 9 | 9 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_new-inve |
| 7 | new-utils-class-connection | ansible_refactor | timed_out | 81.12 | 343646 | 6477 | 0 | 3829 | 18 | 0 | 0 | 0 |  | 7 | 1 | No repository changes detected from Copilot response. |
| 8 | new-utils-from-basic | ansible_refactor | failed | 198.77 | 1135304 | 19063 | 0 | 9509 | 33 | 123 | 91 | 13 |  | 12 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_new-util |
| 9 | parse_key_value | ansible_refactor | success | 81.46 | 413015 | 7112 | 0 | 1088 | 16 | 36 | 32 | 12 | 21 | 21 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_parse_ke |
| 10 | rename-lenient-lowercase | ansible_refactor | success | 44.41 | 180094 | 2321 | 0 | 612 | 9 | 6 | 2 | 2 | 4 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_rename-l |
| 11 | sort-groups-to-group-sort | ansible_refactor | success | 40.61 | 141995 | 1551 | 0 | 480 | 9 | 8 | 4 | 2 | 4 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/ansible_refactor_sort-gro |
| 12 | add-log-parameter-get-digest-algorithm | celery_refactor | success | 39.79 | 166425 | 1638 | 0 | 677 | 9 | 2 | 2 | 2 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_add-log-p |
| 13 | add-log-parameter-node-format | celery_refactor | success | 50.1 | 278362 | 2717 | 0 | 1131 | 14 | 5 | 5 | 3 | 3 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_add-log-p |
| 14 | annotation-utils | celery_refactor | failed | 58.06 | 218279 | 4001 | 0 | 2478 | 12 | 16 | 8 | 2 | 5 | 8 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_annotatio |
| 15 | autoretry-to-retry | celery_refactor | failed | 92.47 | 557917 | 7553 | 0 | 4006 | 24 | 12 | 8 | 7 | 6 | 7 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_autoretry |
| 16 | combine-unpickle-task | celery_refactor | failed | 54.06 | 283329 | 3628 | 0 | 1230 | 15 | 12 | 12 | 3 | 5 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_combine-u |
| 17 | dump-message-to-serialization | celery_refactor | success | 118.89 | 815860 | 5441 | 0 | 1573 | 32 | 10 | 9 | 2 | 3 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_dump-mess |
| 18 | ensure_serialize | celery_refactor | success | 94.75 | 631648 | 7459 | 0 | 2573 | 31 | 13 | 10 | 4 | 9 | 9 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_ensure_se |
| 19 | evaluate-promises-to-serialization | celery_refactor | success | 54.1 | 318984 | 3507 | 0 | 1157 | 13 | 10 | 8 | 2 | 4 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_evaluate- |
| 20 | expand-router-string-to-utils | celery_refactor | failed | 68.33 | 355871 | 4940 | 0 | 2337 | 15 | 11 | 10 | 2 | 3 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_expand-ro |
| 21 | object-mro-lookup | celery_refactor | success | 52.04 | 204045 | 3030 | 0 | 1480 | 12 | 2 | 1 | 1 | 3 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_object-mr |
| 22 | rename-host-format | celery_refactor | failed | 78.47 | 478811 | 5670 | 0 | 1563 | 24 | 10 | 6 | 3 | 6 | 7 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_rename-ho |
| 23 | truncate-text | celery_refactor | failed | 226.85 | 1754752 | 15338 | 0 | 7268 | 46 | 17 | 17 | 7 |  | 9 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/celery_refactor_truncate- |
| 24 | add-log-parameter-constant-time-compare | django_refactor | failed | 98.91 | 593299 | 7126 | 0 | 1811 | 23 | 21 | 13 | 6 | 2 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_add-log-p |
| 25 | add-log-parameter-get-resolver | django_refactor | failed | 183.83 | 1551133 | 14457 | 0 | 4723 | 44 | 32 | 27 | 11 | 2 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_add-log-p |
| 26 | add-log-parameter-resolve-error-handler | django_refactor | failed | 68.3 | 519783 | 4432 | 0 | 1156 | 23 | 13 | 6 | 4 |  | 2 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_add-log-p |
| 27 | add-none-handling-duration-string | django_refactor | success | 66.13 | 302670 | 3618 | 0 | 987 | 15 | 6 | 1 | 3 | 3 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_add-none- |
| 28 | combine-utils-dates-dateformat | django_refactor | success | 68.23 | 329211 | 5221 | 0 | 2519 | 14 | 80 | 11 | 3 | 4 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_combine-u |
| 29 | combine-utils-hashable-itercompat | django_refactor | failed | 216.52 | 1450631 | 23388 | 0 | 11504 | 61 | 63 | 58 | 15 | 3 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_combine-u |
| 30 | new-converter-to-python-class | django_refactor | failed | 50.26 | 165935 | 3087 | 0 | 748 | 8 | 55 | 41 | 1 | 1 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_new-conve |
| 31 | new-path-traversal-exception | django_refactor | failed | 147.5 | 1055977 | 17077 | 0 | 12225 | 31 | 19 | 13 | 6 | 7 | 9 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_new-path- |
| 32 | new-reference-context-field-class | django_refactor | timed_out | 54.46 | 231294 | 2621 | 0 | 1325 | 12 | 0 | 0 | 0 |  | 4 | 1 | No repository changes detected from Copilot response. |
| 33 | new-reference-context-graph-class | django_refactor | failed | 204.55 | 1413902 | 24200 | 0 | 3561 | 32 | 74 | 26 | 4 | 5 | 9 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_new-refer |
| 34 | new-timezone-class | django_refactor | timed_out | 184.11 | 538273 | 20979 | 0 | 18033 | 20 | 0 | 0 | 0 |  | 4 | 1 | No repository changes detected from Copilot response. |
| 35 | new-utils-adapt-method-mode | django_refactor | success | 82.44 | 543322 | 6138 | 0 | 1933 | 24 | 49 | 44 | 2 | 3 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_new-utils |
| 36 | new-utils-check-response | django_refactor | success | 60.11 | 352574 | 3419 | 0 | 1216 | 16 | 39 | 25 | 2 | 2 | 2 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_new-utils |
| 37 | new-utils-path-from-module | django_refactor | success | 82.24 | 447197 | 5696 | 0 | 2866 | 20 | 37 | 29 | 2 | 2 | 2 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_new-utils |
| 38 | remove-core-cache-utils | django_refactor | failed | 58.27 | 279194 | 4135 | 0 | 1098 | 12 | 22 | 17 | 5 | 4 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_remove-co |
| 39 | remove-db-models-constants | django_refactor | success | 444.07 | 1408474 | 50941 | 0 | 40489 | 49 | 39 | 29 | 20 | 19 | 19 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_remove-db |
| 40 | rename-file-move-safe | django_refactor | success | 131.93 | 776536 | 8124 | 0 | 2343 | 25 | 22 | 18 | 5 | 6 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_rename-fi |
| 41 | split-parse-apps-and-model-labels | django_refactor | failed | 52.09 | 192445 | 3534 | 0 | 1680 | 10 | 30 | 9 | 1 | 2 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/django_refactor_split-par |
| 42 | add-log-parameter-generate-option-id-for-path | fastapi_refactor | success | 62.36 | 335401 | 2939 | 0 | 1528 | 15 | 2 | 2 | 2 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/fastapi_refactor_add-log- |
| 43 | exception-handlers-to-handlers | fastapi_refactor | failed | 119.33 | 493946 | 10804 | 0 | 3576 | 22 | 5 | 5 | 5 | 11 | 12 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/fastapi_refactor_exceptio |
| 44 | get-auth-scheme-param | fastapi_refactor | success | 58.38 | 279752 | 3846 | 0 | 1655 | 15 | 6 | 2 | 2 | 6 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/fastapi_refactor_get-auth |
| 45 | openapi-get-utils | fastapi_refactor | success | 68.57 | 336124 | 4543 | 0 | 1630 | 18 | 7 | 7 | 7 | 9 | 9 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/fastapi_refactor_openapi- |
| 46 | params-to-param | fastapi_refactor | failed | 80.45 | 344145 | 5562 | 0 | 2462 | 16 | 0 | 0 | 0 | 10 | 22 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/fastapi_refactor_params-t |
| 47 | value-is-a-sequence | fastapi_refactor | success | 33.89 | 101898 | 1260 | 0 | 264 | 6 | 7 | 3 | 2 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/fastapi_refactor_value-is |
| 48 | add-log-parameter-get-debug-flag | flask_refactor | success | 49.93 | 180958 | 3185 | 0 | 1042 | 10 | 10 | 5 | 4 | 7 | 7 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/flask_refactor_add-log-pa |
| 49 | add-log-parameter-get-flashed-messages | flask_refactor | success | 70.22 | 467217 | 4620 | 0 | 1384 | 22 | 12 | 7 | 2 | 3 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/flask_refactor_add-log-pa |
| 50 | debughelpers-to-helpers.py | flask_refactor | timed_out | 15.36 | 467217 | 4620 | 0 | 1384 | 22 | 12 | 7 | 2 |  | 5 | 1 | No repository changes detected from Copilot response. |
| 51 | rename-send-from-directory | flask_refactor | timed_out | 63.13 | 167329 | 3969 | 0 | 3248 | 10 | 0 | 0 | 0 | 1 | 4 | 1 | No repository changes detected from Copilot response. |
| 52 | render-template-str | flask_refactor | success | 74.38 | 300632 | 6259 | 0 | 1315 | 14 | 18 | 13 | 8 | 10 | 10 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/flask_refactor_render-tem |
| 53 | stream-template-str | flask_refactor | failed | 37.62 | 88354 | 1796 | 0 | 861 | 5 | 4 | 1 | 1 | 3 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/flask_refactor_stream-tem |
| 54 | add-log-parameter-get-encoding-from-headers | requests_refactor | failed | 47.8 | 191494 | 3168 | 0 | 703 | 11 | 4 | 3 | 2 | 2 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_add-log |
| 55 | add-log-parameter-resolve-proxies | requests_refactor | success | 62.04 | 266157 | 3608 | 0 | 946 | 15 | 4 | 3 | 2 | 2 | 2 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_add-log |
| 56 | add-log-parameter-select-proxy | requests_refactor | timed_out | 45.88 | 153295 | 1754 | 0 | 537 | 9 | 0 | 0 | 0 |  | 2 | 1 | No repository changes detected from Copilot response. |
| 57 | combine-from-key-to-key | requests_refactor | success | 84.28 | 368755 | 5637 | 0 | 1723 | 17 | 34 | 45 | 4 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_combine |
| 58 | combine-internal-utils-utils | requests_refactor | failed | 214.26 | 464363 | 28957 | 0 | 25079 | 22 | 45 | 11 | 1 | 1 | 7 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_combine |
| 59 | move-hooks-sessions | requests_refactor | failed | 472.27 | 1943192 | 32042 | 0 | 20098 | 58 | 30 | 8 | 3 | 4 | 7 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_move-ho |
| 60 | new-cookie-utils-class | requests_refactor | failed | 259.88 | 1539499 | 12293 | 0 | 2857 | 46 | 198 | 120 | 1 |  | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_new-coo |
| 61 | rename-lookup-dict-dict-lookup | requests_refactor | success | 51.92 | 229003 | 2981 | 0 | 705 | 11 | 11 | 7 | 3 | 7 | 7 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_rename- |
| 62 | rename-super-len-complex-len | requests_refactor | failed | 68.15 | 249597 | 6059 | 0 | 901 | 11 | 33 | 29 | 3 | 2 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_rename- |
| 63 | split-warnings-exceptions | requests_refactor | success | 86.35 | 494611 | 6231 | 0 | 2477 | 22 | 39 | 25 | 4 | 9 | 9 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/requests_refactor_split-w |
| 64 | add-log-parameter-delete-directory | salt_refactor | success | 47.97 | 170928 | 2727 | 0 | 993 | 9 | 6 | 5 | 2 | 4 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_add-log-par |
| 65 | add-log-parameter-get-capability-definitions | salt_refactor | success | 112.41 | 452729 | 9681 | 0 | 5730 | 23 | 10 | 5 | 2 | 3 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_add-log-par |
| 66 | add-log-parameter-recursive-diff | salt_refactor | success | 121.55 | 583778 | 11353 | 0 | 4885 | 20 | 11 | 6 | 2 | 6 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_add-log-par |
| 67 | cant-create | salt_refactor | failed | 48.69 | 178657 | 2690 | 0 | 1095 | 10 | 6 | 4 | 3 | 6 | 8 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_cant-create |
| 68 | channel-to-transport | salt_refactor | failed | 59.14 | 198533 | 3238 | 0 | 1070 | 10 | 0 | 0 | 0 | 3 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_channel-to- |
| 69 | ex-pillar-fail | salt_refactor | success | 48.33 | 187156 | 2760 | 0 | 1063 | 11 | 1 | 1 | 1 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_ex-pillar-f |
| 70 | ex-state-fail | salt_refactor | failed | 45.12 | 167632 | 2168 | 0 | 674 | 10 | 7 | 4 | 3 | 5 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_ex-state-fa |
| 71 | exactly-n-boto-mod | salt_refactor | failed | 123.61 | 872463 | 6836 | 0 | 3153 | 33 | 4 | 11 | 1 | 2 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_exactly-n-b |
| 72 | get-unavail | salt_refactor | success | 43.57 | 132295 | 1788 | 0 | 469 | 8 | 5 | 4 | 4 | 10 | 10 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_get-unavail |
| 73 | iam-to-aws | salt_refactor | success | 61.48 | 309406 | 3232 | 0 | 1134 | 13 | 35 | 0 | 1 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_iam-to-aws_ |
| 74 | mksls-to-specific | salt_refactor | success | 59.12 | 317413 | 3921 | 0 | 1204 | 14 | 12 | 3 | 3 | 6 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_mksls-to-sp |
| 75 | namecheap-xmlutil | salt_refactor | success | 121.54 | 469001 | 10697 | 0 | 7398 | 17 | 84 | 71 | 2 | 6 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_namecheap-x |
| 76 | paged-call-boto-mod | salt_refactor | failed | 72.86 | 385169 | 4394 | 0 | 2026 | 21 | 2 | 16 | 1 | 1 | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_paged-call- |
| 77 | pem-fingerprint | salt_refactor | success | 73.24 | 340028 | 4939 | 0 | 1311 | 14 | 2 | 2 | 2 | 10 | 10 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_pem-fingerp |
| 78 | perm-denied | salt_refactor | failed | 42.3 | 154555 | 1683 | 0 | 740 | 9 | 3 | 2 | 2 | 4 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/salt_refactor_perm-denied |
| 79 | add-log-parameter-disconnect-all | scrapy_refactor | success | 48.22 | 203577 | 2052 | 0 | 631 | 11 | 8 | 4 | 3 | 6 | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_add-log-p |
| 80 | add-log-parameter-job-dir | scrapy_refactor | failed | 46.22 | 215812 | 2373 | 0 | 666 | 12 | 4 | 4 | 4 | 3 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_add-log-p |
| 81 | add-log-parameter-xmliter | scrapy_refactor | failed | 232.92 | 832646 | 29668 | 0 | 24194 | 30 | 21 | 17 | 2 | 2 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_add-log-p |
| 82 | genspider-functions-to-utils-url | scrapy_refactor | failed | 72.48 | 413225 | 3563 | 0 | 1356 | 21 | 17 | 17 | 2 |  | 4 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_genspider |
| 83 | new-downloadermiddlewares-utils | scrapy_refactor | success | 54.16 | 218705 | 3166 | 0 | 808 | 12 | 29 | 20 | 2 | 5 | 5 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_new-downl |
| 84 | new-spider-utils-in-spiders | scrapy_refactor | timed_out | 842.16 | 809584 | 104692 | 0 | 100268 | 32 | 37 | 0 | 1 | 3 | 8 | 1 | No repository changes detected from Copilot response. |
| 85 | new-verify-reactor-class | scrapy_refactor | failed | 126.36 | 684431 | 8114 | 0 | 2828 | 23 | 59 | 46 | 6 | 8 | 11 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_new-verif |
| 86 | not-supported-exception-to-unsupported | scrapy_refactor | failed | 62.53 | 246069 | 4243 | 0 | 1045 | 10 | 16 | 13 | 6 | 8 | 10 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_not-suppo |
| 87 | parameterize-gunzip | scrapy_refactor | timed_out | 56.17 | 256684 | 2964 | 0 | 1484 | 13 | 0 | 0 | 0 | 1 | 9 | 1 | No repository changes detected from Copilot response. |
| 88 | rename-description-commands | scrapy_refactor | success | 66.69 | 282465 | 4636 | 0 | 1020 | 13 | 27 | 27 | 17 | 7 | 7 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_rename-de |
| 89 | rename-engine-status | scrapy_refactor | success | 70.55 | 309120 | 6210 | 0 | 1673 | 13 | 33 | 27 | 6 | 8 | 8 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_rename-en |
| 90 | rename-processtest-testproc | scrapy_refactor | failed | 60.42 | 272931 | 3290 | 0 | 962 | 11 | 13 | 9 | 5 |  | 6 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_rename-pr |
| 91 | sitemap-url-to-url | scrapy_refactor | failed | 58.34 | 251783 | 3253 | 0 | 651 | 11 | 13 | 1 | 1 | 1 | 3 | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/scrapy_refactor_sitemap-u |
| 92 | global-objects | tornado_refactor | failed | 225.07 | 803221 | 24266 | 0 | 19228 | 26 | 102 | 0 | 2 |  |  | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/tornado_refactor_global-o |
| 93 | log-utils | tornado_refactor | failed | 151.85 | 1047784 | 14280 | 0 | 6313 | 33 | 176 | 137 | 4 |  |  | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/tornado_refactor_log-util |
| 94 | option-parser-with-pretty-print | tornado_refactor | failed | 188.19 | 943409 | 15132 | 0 | 8858 | 30 | 125 | 110 | 2 |  |  | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/tornado_refactor_option-p |
| 95 | options-utils | tornado_refactor | failed | 204.68 | 967234 | 19467 | 0 | 12962 | 31 | 272 | 79 | 2 |  |  | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/tornado_refactor_options- |
| 96 | remove-locale-data | tornado_refactor | failed | 84.59 | 411546 | 7176 | 0 | 1677 | 19 | 69 | 67 | 2 |  |  | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/tornado_refactor_remove-l |
| 97 | rename-http1connection | tornado_refactor | timed_out | 32.2 | 46357 | 354 | 0 | 179 | 3 | 0 | 0 | 0 |  |  | 1 | No repository changes detected from Copilot response. |
| 98 | rename-to-camel-case | tornado_refactor | failed | 72.75 | 390905 | 5407 | 0 | 2362 | 18 | 9 | 7 | 2 |  |  | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/tornado_refactor_rename-t |
| 99 | resolvers-as-separate | tornado_refactor | timed_out | 194.35 | 1136122 | 14093 | 0 | 6055 | 44 | 290 | 0 | 1 |  |  | 1 | No repository changes detected from Copilot response. |
| 100 | tcpclient-connect-params | tornado_refactor | failed | 226.76 | 1983670 | 19374 | 0 | 7420 | 49 | 173 | 20 | 7 |  |  | 0 | /workspace/benchmarks/refactorbench/outputs/workspaces/tornado_refactor_tcpclien |

---

### Run 4: deepseek-v4-pro S1 desc RefactorBench
Source: `deepseek_s1_descriptive_refbench.csv` | Rows: 100 | Columns: 9

| Nr | Repo | TaskId | Passed | TestSucceeded | ApplySucceeded | Duration(s) |
|---|---|---|---|---|---|---|
| 1 | ansible_refactor | add-log-parameter-get-group-vars | True | True | True | 169.4 |
| 2 | ansible_refactor | add-log-parameter-is-systemd-managed | True | True | True | 139.3 |
| 3 | ansible_refactor | combine-namespace-compat | True | True | True | 190.2 |
| 4 | ansible_refactor | data-to-inventory-data | True | True | True | 124.9 |
| 5 | ansible_refactor | move-quoting-splitter | True | True | True | 176.8 |
| 6 | ansible_refactor | new-inventory-patterns | True | True | True | 302.8 |
| 7 | ansible_refactor | new-utils-class-connection | True | True | True | 180.6 |
| 8 | ansible_refactor | new-utils-from-basic | False | False | True | 332.5 |
| 9 | ansible_refactor | parse_key_value | True | True | True | 314.1 |
| 10 | ansible_refactor | rename-lenient-lowercase | True | True | True | 198.3 |
| 11 | ansible_refactor | sort-groups-to-group-sort | True | True | True | 96.5 |
| 12 | celery_refactor | add-log-parameter-get-digest-algorithm | True | True | True | 86.1 |
| 13 | celery_refactor | add-log-parameter-node-format | True | True | True | 118.1 |
| 14 | celery_refactor | annotation-utils | False | False | True | 135.9 |
| 15 | celery_refactor | autoretry-to-retry | True | True | True | 169.0 |
| 16 | celery_refactor | combine-unpickle-task | False | False | True | 112.0 |
| 17 | celery_refactor | dump-message-to-serialization | True | True | True | 113.3 |
| 18 | celery_refactor | ensure_serialize | True | True | True | 127.4 |
| 19 | celery_refactor | evaluate-promises-to-serialization | True | True | True | 196.7 |
| 20 | celery_refactor | expand-router-string-to-utils | True | True | True | 147.8 |
| 21 | celery_refactor | object-mro-lookup | True | True | True | 77.7 |
| 22 | celery_refactor | rename-host-format | True | True | True | 93.8 |
| 23 | celery_refactor | truncate-text | True | True | True | 124.3 |
| 24 | django_refactor | add-log-parameter-constant-time-compare | False | False | True | 189.3 |
| 25 | django_refactor | add-log-parameter-get-resolver | False | False | True | 237.5 |
| 26 | django_refactor | add-log-parameter-resolve-error-handler | False | False | True | 188.4 |
| 27 | django_refactor | add-none-handling-duration-string | False | False | True | 166.2 |
| 28 | django_refactor | combine-utils-dates-dateformat | True | True | True | 195.5 |
| 29 | django_refactor | combine-utils-hashable-itercompat | True | True | True | 138.2 |
| 30 | django_refactor | new-converter-to-python-class | True | True | True | 190.2 |
| 31 | django_refactor | new-path-traversal-exception | False | False | True | 785.9 |
| 32 | django_refactor | new-reference-context-field-class | False | False | True | 324.3 |
| 33 | django_refactor | new-reference-context-graph-class | True | True | True | 510.9 |
| 34 | django_refactor | new-timezone-class | True | True | True | 153.0 |
| 35 | django_refactor | new-utils-adapt-method-mode | True | True | True | 207.1 |
| 36 | django_refactor | new-utils-check-response | True | True | True | 200.4 |
| 37 | django_refactor | new-utils-path-from-module | True | True | True | 126.4 |
| 38 | django_refactor | remove-core-cache-utils | True | True | True | 151.2 |
| 39 | django_refactor | remove-db-models-constants | True | True | True | 272.8 |
| 40 | django_refactor | rename-file-move-safe | True | True | True | 163.7 |
| 41 | django_refactor | split-parse-apps-and-model-labels | True | True | True | 148.3 |
| 42 | fastapi_refactor | add-log-parameter-generate-option-id-for-path | True | True | True | 142.3 |
| 43 | fastapi_refactor | exception-handlers-to-handlers | True | True | True | 114.4 |
| 44 | fastapi_refactor | get-auth-scheme-param | True | True | True | 173.9 |
| 45 | fastapi_refactor | openapi-get-utils | True | True | True | 191.4 |
| 46 | fastapi_refactor | params-to-param | False | False | True | 420.8 |
| 47 | fastapi_refactor | value-is-a-sequence | True | True | True | 158.3 |
| 48 | flask_refactor | add-log-parameter-get-debug-flag | True | True | True | 160.4 |
| 49 | flask_refactor | add-log-parameter-get-flashed-messages | True | True | True | 95.4 |
| 50 | flask_refactor | debughelpers-to-helpers.py | False | False | False | 22.4 |
| 51 | flask_refactor | rename-send-from-directory | True | True | True | 151.0 |
| 52 | flask_refactor | render-template-str | True | True | True | 204.6 |
| 53 | flask_refactor | stream-template-str | True | True | True | 113.9 |
| 54 | requests_refactor | add-log-parameter-get-encoding-from-headers | True | True | True | 112.1 |
| 55 | requests_refactor | add-log-parameter-resolve-proxies | True | True | True | 97.8 |
| 56 | requests_refactor | add-log-parameter-select-proxy | True | True | True | 113.8 |
| 57 | requests_refactor | combine-from-key-to-key | True | True | True | 268.9 |
| 58 | requests_refactor | combine-internal-utils-utils | True | True | True | 481.3 |
| 59 | requests_refactor | move-hooks-sessions | True | True | True | 392.2 |
| 60 | requests_refactor | new-cookie-utils-class | True | True | True | 342.8 |
| 61 | requests_refactor | rename-lookup-dict-dict-lookup | True | True | True | 120.1 |
| 62 | requests_refactor | rename-super-len-complex-len | True | True | True | 207.9 |
| 63 | requests_refactor | split-warnings-exceptions | True | True | True | 792.7 |
| 64 | salt_refactor | add-log-parameter-delete-directory | True | True | True | 172.2 |
| 65 | salt_refactor | add-log-parameter-get-capability-definitions | True | True | True | 111.6 |
| 66 | salt_refactor | add-log-parameter-recursive-diff | True | True | True | 342.6 |
| 67 | salt_refactor | cant-create | True | True | True | 95.6 |
| 68 | salt_refactor | channel-to-transport | True | True | True | 131.5 |
| 69 | salt_refactor | ex-pillar-fail | True | True | True | 125.6 |
| 70 | salt_refactor | ex-state-fail | True | True | True | 151.6 |
| 71 | salt_refactor | exactly-n-boto-mod | False | False | True | 180.1 |
| 72 | salt_refactor | get-unavail | True | True | True | 114.8 |
| 73 | salt_refactor | iam-to-aws | True | True | True | 106.2 |
| 74 | salt_refactor | mksls-to-specific | True | True | True | 95.0 |
| 75 | salt_refactor | namecheap-xmlutil | True | True | True | 235.4 |
| 76 | salt_refactor | paged-call-boto-mod | True | True | True | 153.9 |
| 77 | salt_refactor | pem-fingerprint | True | True | True | 196.3 |
| 78 | salt_refactor | perm-denied | True | True | True | 155.8 |
| 79 | scrapy_refactor | add-log-parameter-disconnect-all | True | True | True | 118.7 |
| 80 | scrapy_refactor | add-log-parameter-job-dir | True | True | True | 173.8 |
| 81 | scrapy_refactor | add-log-parameter-xmliter | True | True | True | 150.6 |
| 82 | scrapy_refactor | genspider-functions-to-utils-url | True | True | True | 114.1 |
| 83 | scrapy_refactor | new-downloadermiddlewares-utils | True | True | True | 166.9 |
| 84 | scrapy_refactor | new-spider-utils-in-spiders | True | True | True | 308.6 |
| 85 | scrapy_refactor | new-verify-reactor-class | False | False | True | 187.2 |
| 86 | scrapy_refactor | not-supported-exception-to-unsupported | True | True | True | 156.9 |
| 87 | scrapy_refactor | parameterize-gunzip | False | False | True | 215.7 |
| 88 | scrapy_refactor | rename-description-commands | True | True | True | 175.3 |
| 89 | scrapy_refactor | rename-engine-status | True | True | True | 154.7 |
| 90 | scrapy_refactor | rename-processtest-testproc | True | True | True | 148.6 |
| 91 | scrapy_refactor | sitemap-url-to-url | True | True | True | 251.4 |
| 92 | tornado_refactor | global-objects | False | False | True | 462.2 |
| 93 | tornado_refactor | log-utils | False | False | True | 258.0 |
| 94 | tornado_refactor | option-parser-with-pretty-print | False | False | True | 677.1 |
| 95 | tornado_refactor | options-utils | False | False | True | 839.0 |
| 96 | tornado_refactor | remove-locale-data | False | False | True | 132.7 |
| 97 | tornado_refactor | rename-http1connection | False | False | True | 116.0 |
| 98 | tornado_refactor | rename-to-camel-case | False | False | True | 168.0 |
| 99 | tornado_refactor | resolvers-as-separate | False | False | True | 695.0 |
| 100 | tornado_refactor | tcpclient-connect-params | False | False | True | 518.4 |

---

### Run 5: minimax-m3 S1 desc RefactorBench
Source: `minimax_s1_descriptive_refbench.csv` | Rows: 100 | Columns: 9

| Nr | Repo | TaskId | Passed | TestSucceeded | ApplySucceeded | Duration(s) |
|---|---|---|---|---|---|---|
| 1 | ansible_refactor | add-log-parameter-get-group-vars | True | True | True | 127.8 |
| 2 | ansible_refactor | add-log-parameter-is-systemd-managed | True | True | True | 97.0 |
| 3 | ansible_refactor | combine-namespace-compat | True | True | True | 234.8 |
| 4 | ansible_refactor | data-to-inventory-data | True | True | True | 66.0 |
| 5 | ansible_refactor | move-quoting-splitter | True | True | True | 139.4 |
| 6 | ansible_refactor | new-inventory-patterns | True | True | True | 229.2 |
| 7 | ansible_refactor | new-utils-class-connection | True | True | True | 228.6 |
| 8 | ansible_refactor | new-utils-from-basic | False | False | True | 413.7 |
| 9 | ansible_refactor | parse_key_value | True | True | True | 249.4 |
| 10 | ansible_refactor | rename-lenient-lowercase | True | True | True | 153.5 |
| 11 | ansible_refactor | sort-groups-to-group-sort | True | True | True | 88.2 |
| 12 | celery_refactor | add-log-parameter-get-digest-algorithm | True | True | True | 114.2 |
| 13 | celery_refactor | add-log-parameter-node-format | True | True | True | 87.6 |
| 14 | celery_refactor | annotation-utils | False | False | True | 152.0 |
| 15 | celery_refactor | autoretry-to-retry | True | True | True | 150.6 |
| 16 | celery_refactor | combine-unpickle-task | False | False | True | 122.2 |
| 17 | celery_refactor | dump-message-to-serialization | True | True | True | 155.9 |
| 18 | celery_refactor | ensure_serialize | True | True | True | 159.6 |
| 19 | celery_refactor | evaluate-promises-to-serialization | True | True | True | 180.2 |
| 20 | celery_refactor | expand-router-string-to-utils | True | True | True | 146.1 |
| 21 | celery_refactor | object-mro-lookup | True | True | True | 69.4 |
| 22 | celery_refactor | rename-host-format | True | True | True | 109.9 |
| 23 | celery_refactor | truncate-text | True | True | True | 183.2 |
| 24 | django_refactor | add-log-parameter-constant-time-compare | False | False | True | 154.8 |
| 25 | django_refactor | add-log-parameter-get-resolver | False | False | True | 146.4 |
| 26 | django_refactor | add-log-parameter-resolve-error-handler | False | False | True | 204.4 |
| 27 | django_refactor | add-none-handling-duration-string | False | False | True | 132.1 |
| 28 | django_refactor | combine-utils-dates-dateformat | True | True | True | 213.7 |
| 29 | django_refactor | combine-utils-hashable-itercompat | True | True | True | 136.3 |
| 30 | django_refactor | new-converter-to-python-class | True | True | True | 381.2 |
| 31 | django_refactor | new-path-traversal-exception | False | False | True | 629.1 |
| 32 | django_refactor | new-reference-context-field-class | True | True | True | 257.9 |
| 33 | django_refactor | new-reference-context-graph-class | True | True | True | 312.4 |
| 34 | django_refactor | new-timezone-class | True | True | True | 124.4 |
| 35 | django_refactor | new-utils-adapt-method-mode | True | True | True | 164.5 |
| 36 | django_refactor | new-utils-check-response | True | True | True | 143.7 |
| 37 | django_refactor | new-utils-path-from-module | True | True | True | 130.3 |
| 38 | django_refactor | remove-core-cache-utils | False | False | True | 155.7 |
| 39 | django_refactor | remove-db-models-constants | False | False | False | 1526.9 |
| 40 | django_refactor | rename-file-move-safe | True | True | True | 164.3 |
| 41 | django_refactor | split-parse-apps-and-model-labels | True | True | True | 106.0 |
| 42 | fastapi_refactor | add-log-parameter-generate-option-id-for-path | True | True | True | 109.6 |
| 43 | fastapi_refactor | exception-handlers-to-handlers | True | True | True | 297.0 |
| 44 | fastapi_refactor | get-auth-scheme-param | True | True | True | 146.2 |
| 45 | fastapi_refactor | openapi-get-utils | True | True | True | 152.8 |
| 46 | fastapi_refactor | params-to-param | True | True | True | 374.3 |
| 47 | fastapi_refactor | value-is-a-sequence | True | True | True | 148.4 |
| 48 | flask_refactor | add-log-parameter-get-debug-flag | True | True | True | 168.7 |
| 49 | flask_refactor | add-log-parameter-get-flashed-messages | True | True | True | 148.6 |
| 50 | flask_refactor | debughelpers-to-helpers.py | False | False | False | 22.6 |
| 51 | flask_refactor | rename-send-from-directory | False | False | True | 294.0 |
| 52 | flask_refactor | render-template-str | True | True | True | 161.8 |
| 53 | flask_refactor | stream-template-str | True | True | True | 65.5 |
| 54 | requests_refactor | add-log-parameter-get-encoding-from-headers | True | True | True | 205.2 |
| 55 | requests_refactor | add-log-parameter-resolve-proxies | True | True | True | 63.2 |
| 56 | requests_refactor | add-log-parameter-select-proxy | True | True | True | 75.5 |
| 57 | requests_refactor | combine-from-key-to-key | True | True | True | 151.3 |
| 58 | requests_refactor | combine-internal-utils-utils | True | True | True | 298.6 |
| 59 | requests_refactor | move-hooks-sessions | True | True | True | 475.2 |
| 60 | requests_refactor | new-cookie-utils-class | True | True | True | 355.9 |
| 61 | requests_refactor | rename-lookup-dict-dict-lookup | True | True | True | 83.8 |
| 62 | requests_refactor | rename-super-len-complex-len | True | True | True | 177.6 |
| 63 | requests_refactor | split-warnings-exceptions | True | True | True | 857.5 |
| 64 | salt_refactor | add-log-parameter-delete-directory | True | True | True | 168.5 |
| 65 | salt_refactor | add-log-parameter-get-capability-definitions | True | True | True | 111.2 |
| 66 | salt_refactor | add-log-parameter-recursive-diff | True | True | True | 192.5 |
| 67 | salt_refactor | cant-create | True | True | True | 73.1 |
| 68 | salt_refactor | channel-to-transport | True | True | True | 121.3 |
| 69 | salt_refactor | ex-pillar-fail | True | True | True | 93.2 |
| 70 | salt_refactor | ex-state-fail | True | True | True | 105.0 |
| 71 | salt_refactor | exactly-n-boto-mod | True | True | True | 158.1 |
| 72 | salt_refactor | get-unavail | True | True | True | 118.9 |
| 73 | salt_refactor | iam-to-aws | True | True | True | 124.5 |
| 74 | salt_refactor | mksls-to-specific | True | True | True | 123.1 |
| 75 | salt_refactor | namecheap-xmlutil | True | True | True | 197.0 |
| 76 | salt_refactor | paged-call-boto-mod | True | True | True | 245.2 |
| 77 | salt_refactor | pem-fingerprint | False | False | True | 147.6 |
| 78 | salt_refactor | perm-denied | True | True | True | 88.9 |
| 79 | scrapy_refactor | add-log-parameter-disconnect-all | True | True | True | 77.7 |
| 80 | scrapy_refactor | add-log-parameter-job-dir | True | True | True | 111.3 |
| 81 | scrapy_refactor | add-log-parameter-xmliter | True | True | True | 911.4 |
| 82 | scrapy_refactor | genspider-functions-to-utils-url | True | True | True | 114.8 |
| 83 | scrapy_refactor | new-downloadermiddlewares-utils | True | True | True | 108.2 |
| 84 | scrapy_refactor | new-spider-utils-in-spiders | True | True | True | 206.9 |
| 85 | scrapy_refactor | new-verify-reactor-class | False | False | True | 142.6 |
| 86 | scrapy_refactor | not-supported-exception-to-unsupported | True | True | True | 136.5 |
| 87 | scrapy_refactor | parameterize-gunzip | False | False | True | 235.9 |
| 88 | scrapy_refactor | rename-description-commands | False | False | True | 61.6 |
| 89 | scrapy_refactor | rename-engine-status | True | True | True | 118.2 |
| 90 | scrapy_refactor | rename-processtest-testproc | True | True | True | 81.6 |
| 91 | scrapy_refactor | sitemap-url-to-url | True | True | True | 170.4 |
| 92 | tornado_refactor | global-objects | False | False | True | 265.2 |
| 93 | tornado_refactor | log-utils | False | False | True | 154.3 |
| 94 | tornado_refactor | option-parser-with-pretty-print | False | False | True | 368.9 |
| 95 | tornado_refactor | options-utils | False | False | True | 774.0 |
| 96 | tornado_refactor | remove-locale-data | False | False | True | 102.3 |
| 97 | tornado_refactor | rename-http1connection | False | False | True | 172.9 |
| 98 | tornado_refactor | rename-to-camel-case | False | False | True | 178.2 |
| 99 | tornado_refactor | resolvers-as-separate | False | False | True | 439.2 |
| 100 | tornado_refactor | tcpclient-connect-params | False | False | True | 228.3 |

---

### Run 7: deepseek-v4-pro S1-eval RefactorBench
Source: `s1_eval_loop_deepseek_refbench.csv` | Rows: 10 | Columns: 19

| # | Task | Status | Input | Output | Cache | Reasoning | Time | Reqs | +Lines | -Lines | Files | Apply | Test | Result | EvalLoops | lspActions | lspMarkers | completedAt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | annotation-utils | completed | 247.6k | 4.5k | 143.7k | 1.9k | 1m45s | 14 | 17 | 5 | 3 | yes | yes | PASSED | 1 | 4 | diagnostic;find_references;go_to_definition;hover | 2026-05-23T22:16:21Z |
| 2 | add-log-parameter-get-resolver | completed | 807.8k | 8.8k | 420.0k | 2.1k | 3m24s | 27 | 25 | 19 | 8 | yes | yes | PASSED | 1 | 4 | diagnostic;find_references;go_to_definition;hover | 2026-05-23T22:23:54Z |
| 3 | add-log-parameter-resolve-error-handler | completed | 160.9k | 3.5k | 63.4k | 902 | 1m21s | 10 | 6 | 6 | 4 | yes | yes | PASSED | 1 | 4 | diagnostic;find_references;go_to_definition;hover | 2026-05-23T22:27:55Z |
| 4 | paged-call-boto-mod | completed | 292.8k | 6.2k | 128.4k | 3.7k | 2m11s | 13 | 2 | 9 | 1 | yes | yes | PASSED | 0 | 4 | diagnostic;find_references;go_to_definition;hover | 2026-05-23T22:30:09Z |
| Run ID | eval_loop_deepseek_20260523 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Status | completed |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Datasets | refbench |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Setups | s1_default + eval_loop(max=2) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Failed | 0 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Success rate | 4/4 (100%) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

### Run 8: deepseek-v4-pro S3 RefactorBench (19 tasks)
Source: `s3_deepseek_descriptive_refbench_never_passed.csv` | Rows: 19 | Columns: 14
  # RefactorBench S3 Multi-Agent (deepseek/deepseek-v4-pro) | "# 19 never-passed tasks, descriptive mode" | # Pattern: Supervisor -> Analyst -> Modifier -> Validator -> Fix cycle | # Total: 1/19 passed (5.3%)

| # | Repo | TaskId | Passed | Duration(s) | InputTok | OutputTok | CacheRead | Requests | APIDur(s) | LinesAdd | LinesDel | FilesMod | FailReason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ansible_refactor | new-utils-from-basic | False | 531 | 963037 | 24649 | 645632 | 43 | 567 | 110 | 92 | 13 | Apply failed - incomplete edits |
| 2 | celery_refactor | annotation-utils | False | 225 | 387382 | 9957 | 256000 | 25 | 248 | 12 | 7 | 3 | Apply failed - missed import updates |
| 3 | celery_refactor | combine-unpickle-task | False | 213 | 488147 | 9881 | 79488 | 29 | 219 | 6 | 10 | 3 | Apply failed - partial refactor |
| 4 | django_refactor | add-log-parameter-constant-time-compare | False | 350 | 488147 | 9881 | 79488 | 29 | 219 | 6 | 10 | 3 | Test failed - missed call sites |
| 5 | django_refactor | add-log-parameter-get-resolver | False | 592 | 677835 | 18814 | 493952 | 28 | 348 | 21 | 15 | 7 | Test failed - indentation error |
| 6 | django_refactor | add-log-parameter-resolve-error-handler | False | 469 | 328003 | 11155 | 12672 | 21 | 449 | 11 | 6 | 4 | Test failed - missed call sites |
| 7 | django_refactor | new-path-traversal-exception | False | 604 | 1006414 | 20811 | 354304 | 39 | 585 | 26 | 19 | 5 | Timeout - model looped |
| 8 | flask_refactor | debughelpers-to-helpers.py | False | 1 | 487349 | 7510 | 42446 | 33 | 231 | 32 | 0 | 1 | Crash - used wrong model (openrouter/free) |
| 9 | scrapy_refactor | new-verify-reactor-class | True | 573 | 912508 | 30925 | 207104 | 41 | 557 | 54 | 52 | 6 | PASSED |
| 10 | scrapy_refactor | parameterize-gunzip | False | 301 | 668853 | 13710 | 160512 | 35 | 297 | 22 | 16 | 5 | Test failed - wrong parameter name |
| 11 | tornado_refactor | global-objects | False | 292 | 416505 | 13498 | 90112 | 23 | 279 | 46 | 25 | 4 | Test failed (revalidation: workspace cleaned) |
| 12 | tornado_refactor | log-utils | False | 333 | 431411 | 13199 | 98816 | 22 | 319 | 155 | 131 | 4 | Test failed (revalidation: workspace cleaned) |
| 13 | tornado_refactor | option-parser-with-pretty-print | False | 604 | 904055 | 20540 | 259200 | 39 | 590 | 53 | 55 | 3 | Test failed (revalidation: workspace cleaned) |
| 14 | tornado_refactor | options-utils | False | 605 | 1266735 | 26832 | 821376 | 42 | 573 | 145 | 114 | 28 | Test failed (revalidation: workspace cleaned) |
| 15 | tornado_refactor | remove-locale-data | False | 249 | 496361 | 7832 | 196480 | 23 | 232 | 64 | 1 | 1 | Test failed - 2/3 assertions wrong (revalidated) |
| 16 | tornado_refactor | rename-http1connection | False | 320 | 352934 | 14296 | 150144 | 23 | 302 | 12 | 12 | 5 | Test failed - 6/6 assertions wrong (revalidated) |
| 17 | tornado_refactor | rename-to-camel-case | False | 204 | 337589 | 7979 | 214528 | 21 | 205 | 8 | 8 | 2 | Test failed - 4/4 assertions wrong (revalidated) |
| 18 | tornado_refactor | resolvers-as-separate | False | 604 | 760586 | 27196 | 401280 | 34 | 635 | 301 | 277 | 2 | Test failed - 18/18 assertions wrong (revalidated) |
| 19 | tornado_refactor | tcpclient-connect-params | False | 604 | 747473 | 17098 | 404608 | 30 | 562 | 80 | 41 | 5 | Test failed - 6/6 assertions wrong (revalidated) |

---

### Run 9: openrouter/free S1 RefactorBench
Source: `s1_free_refbench.csv` | Rows: 104 | Columns: 18
  Run ID,benchmark_pipeline_20260514_223318 | Status,completed | Model,openrouter/free | Datasets,refbench

| # | Task | Status | Input | Output | Cache | Time | Evals | Cmpct | Reqs | +Lines | -Lines | Files | Model | Build/Test | Model mismatch | Result | Checks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | rs_1778798007746 | completed | 110.8k | 1.7k | 15.1k | 51s | 0 | 0 | 7 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 2 | ed_1778798073671 | completed | 544.1k | 7.8k | 36.7k | 4m29s | 0 | 0 | 24 | 3 | 2 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 3 | at_1778798351380 | completed | 97.1k | 702 | 7.0k | 27s | 0 | 0 | 6 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 4 | ta_1778798389364 | completed | 417.9k | 6.9k | 7.6k | 2m59s | 0 | 0 | 20 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 5 | er_1778798589760 | completed | 601.8k | 5.8k | 61.4k | 3m23s | 0 | 0 | 20 | 5 | 5 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 6 | ns_1778798800573 | terminated | 669.6k | 9.0k | 137.0k | 4m45s | 0 | 0 | 34 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 7 | on_1778799099262 | completed | 282.8k | 3.7k | 30.5k | 1m42s | 0 | 0 | 15 | 41 | 31 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 8 | ic_1778799214874 | completed | 273.8k | 3.0k | 6.0k | 2m49s | 0 | 0 | 13 | 78 | 2 | 1 | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 9 | ue_1778799397600 | terminated | 1.4M | 14.2k | 86.0k | 7m32s | 0 | 0 | 36 | 3 | 3 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 10 | se_1778799863876 | completed | 14.9k | 4 | '- | 3s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 11 | rt_1778799881987 | terminated | 167.7k | 2.6k | 12.3k | 1m25s | 0 | 0 | 11 | 4 | 4 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 12 | hm_1778799975689 | completed | 170.5k | 1.6k | 20.2k | 2m14s | 0 | 0 | 8 | 3 | 3 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 13 | at_1778800121102 | completed | 91.6k | 676 | 17.2k | 24s | 0 | 0 | 6 | 3 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 14 | ls_1778800156002 | completed | 357.5k | 9.2k | 40.5k | 3m16s | 0 | 0 | 18 | 13 | 10 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 15 | ry_1778800361562 | terminated | 518.9k | 7.2k | 23.3k | 3m49s | 0 | 0 | 23 | 4 | 4 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 16 | sk_1778800597496 | completed | 394.5k | 3.4k | 2.0k | 5m52s | 0 | 0 | 18 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 17 | on_1778800959440 | completed | 471.4k | 14.4k | 688 | 5m09s | 0 | 0 | 21 | 12 | 7 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 18 | ze_1778801278191 | completed | 61.6k | 1.4k | 43 | 34s | 0 | 0 | 4 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 19 | on_1778801322417 | completed | 207.4k | 9.1k | 24.3k | 5m04s | 0 | 0 | 8 | 1 | 5 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 20 | ls_1778801635493 | completed | 292.9k | 8.3k | 7.6k | 3m12s | 0 | 0 | 16 | 14 | 6 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 21 | up_1778801836346 | terminated | 30.4k | 375 | '- | 12s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 22 | at_1778801858279 | completed | 159.4k | 6.3k | 16.1k | 1m52s | 0 | 0 | 9 | 5 | 5 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 23 | xt_1778801979802 | completed | 689.2k | 8.8k | 110.0k | 7m53s | 0 | 0 | 31 | 9 | 9 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 24 | re_1778803086762 | completed | 339.3k | 2.8k | 66.3k | 2m30s | 0 | 0 | 18 | 12 | 2 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 25 | er_1778803262394 | completed | 630.8k | 3.9k | 72.9k | 6m43s | 0 | 0 | 29 | 5 | 5 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 26 | er_1778803922401 | terminated | 792.9k | 11.7k | 110.6k | 6m37s | 0 | 0 | 38 | 7 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 27 | ng_1778804520446 | terminated | 320.4k | 4.1k | 52.3k | 3m16s | 0 | 0 | 18 | 17 | 11 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 28 | at_1778804727082 | completed | 435.3k | 10.0k | 35.2k | 7m07s | 0 | 0 | 21 | 86 | 87 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 29 | at_1778805169914 | completed | 184.4k | 4.3k | 16.4k | 3m19s | 0 | 0 | 12 | 33 | 12 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 30 | ss_1778805385345 | terminated | 255.7k | 3.8k | 608 | 2m19s | 0 | 0 | 13 | '- | '- | '- | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 31 | on_1778805696314 | completed | 97.3k | 9.8k | 43 | 1m46s | 0 | 0 | 6 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 32 | ss_1778805818201 | completed | 256.1k | 5.2k | 13.3k | 3m28s | 0 | 0 | 12 | 54 | 7 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 33 | ss_1778806838594 | terminated | 1.3M | 9.1k | 95.9k | 10m04s | 0 | 0 | 42 | 18 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 34 | ss_1778807462076 | completed | 195.8k | 6.9k | 18.1k | 4m01s | 0 | 0 | 10 | 33 | 31 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 35 | de_1778807714519 | completed | 526.5k | 5.5k | 39.7k | 2m53s | 0 | 0 | 25 | 43 | 36 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 36 | se_1778807906263 | completed | 576.2k | 15.5k | 79.2k | 7m01s | 0 | 0 | 35 | 11 | 4 | 2 | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 37 | le_1778808347948 | completed | 186.8k | 2.5k | 24.7k | 1m34s | 0 | 0 | 10 | 43 | 1 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 38 | ls_1778808457465 | completed | 575.5k | 19.9k | 59.7k | 6m14s | 0 | 0 | 28 | 15 | 10 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 39 | ts_1778808850618 | completed | 202.4k | 4.0k | 21.9k | 2m09s | 0 | 0 | 12 | 3 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 40 | fe_1778808997030 | terminated | 167.1k | 1.7k | 528 | 1m08s | 0 | 0 | 9 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 41 | ls_1778809079128 | completed | 177.0k | 6.7k | 19.5k | 2m55s | 0 | 0 | 11 | 25 | 16 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 42 | '-path_1778809270 | completed | 294.8k | 4.6k | 491 | 2m15s | 0 | 0 | 18 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 43 | rs_1778809417476 | completed | 191.2k | 9.9k | 160 | 12m30s | 0 | 0 | 12 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 44 | am_1778810179788 | completed | 128.7k | 1.1k | 384 | 58s | 0 | 0 | 7 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 45 | ls_1778810249892 | terminated | 340.9k | 7.8k | 38.0k | 3m03s | 0 | 0 | 19 | 6 | 6 | 6 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 46 | am_1778810441210 | completed | 870.5k | 7.8k | 102.6k | 7m04s | 0 | 0 | 33 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 47 | ce_1778810882164 | completed | 194.9k | 2.5k | 32.2k | 2m11s | 0 | 0 | 13 | 3 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 48 | ag_1778811026349 | completed | 272.5k | 3.6k | 41.3k | 3m03s | 0 | 0 | 15 | 3 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 49 | es_1778811219869 | completed | 344.2k | 4.4k | 7.6k | 2m46s | 0 | 0 | 20 | 3 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 50 | py_1778811395266 | completed | 344.2k | 4.4k | 7.6k | 2m46s | 0 | 0 | 20 | 3 | 1 | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 51 | ry_1778811397562 | terminated | 64.1k | 562 | 448 | 18s | 0 | 0 | 4 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 52 | tr_1778811666822 | terminated | 452.4k | 8.8k | 28.7k | 5m56s | 0 | 0 | 21 | 6 | 6 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 53 | tr_1778812029118 | completed | 474.2k | 7.4k | 72.2k | 4m13s | 0 | 0 | 26 | 4 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 54 | ders_17788122901 | completed | 412.4k | 5.6k | 33.6k | 3m50s | 0 | 0 | 25 | 4 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 55 | es_1778812532428 | terminated | 250.7k | 3.3k | 1.7k | 2m32s | 0 | 0 | 15 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 56 | xy_1778812695064 | terminated | 372.8k | 2.4k | 47.0k | 1m39s | 0 | 0 | 19 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 57 | ey_1778813050824 | terminated | 267.8k | 2.5k | 60.1k | 2m37s | 0 | 0 | 16 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 58 | ls_1778813215406 | completed | 215.8k | 2.1k | 17.5k | 1m34s | 0 | 0 | 12 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 59 | ns_1778813868681 | terminated | 546.5k | 12.3k | 20.2k | 10m20s | 0 | 0 | 26 | 37 | 4 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 60 | ss_1778814496738 | terminated | 93.1k | 859 | 14.5k | 1m11s | 0 | 0 | 6 | 33 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 61 | up_1778814573585 | completed | 203.5k | 1.9k | 18.6k | 1m42s | 0 | 0 | 11 | 4 | 4 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 62 | en_1778814685929 | completed | 159.3k | 1.9k | 16.9k | 1m45s | 0 | 0 | 9 | 2 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 63 | ns_1778814801764 | terminated | 273.2k | 5.0k | 25.5k | 3m02s | 0 | 0 | 15 | 8 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 64 | ry_1778814990601 | terminated | 307.5k | 3.2k | 28.6k | 1m25s | 0 | 0 | 15 | 9 | 6 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 65 | ns_1778815089795 | completed | 136.2k | 8.6k | 6.2k | 2m24s | 0 | 0 | 8 | 27 | 9 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 66 | ff_1778815246706 | completed | 169.6k | 702 | 7.1k | 49s | 0 | 0 | 9 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 67 | te_1778815308272 | completed | 287.4k | 2.2k | 67.5k | 1m44s | 0 | 0 | 14 | 4 | 4 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 68 | rt_1778815426542 | terminated | 444.0k | 3.9k | 67.4k | 3m15s | 0 | 0 | 22 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 69 | il_1778815636699 | completed | 301.3k | 4.3k | 49.2k | 2m59s | 0 | 0 | 16 | 3 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 70 | il_1778815831407 | terminated | 330.2k | 2.4k | 19.2k | 3m54s | 0 | 0 | 19 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 71 | od_1778816080247 | completed | 210.8k | 4.9k | 6.7k | 3m10s | 0 | 0 | 11 | 15 | 197 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 72 | il_1778816284674 | completed | 158.7k | 3.4k | 528 | 1m22s | 0 | 0 | 10 | 4 | 4 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 73 | ws_1778816375002 | completed | 438.7k | 18.2k | 12.3k | 5m44s | 0 | 0 | 21 | '- | '- | '- | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 74 | ic_1778816740283 | completed | 472.4k | 7.2k | 48.4k | 3m24s | 0 | 0 | 25 | 3 | 3 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 75 | il_1778816955291 | completed | 513.7k | 14.9k | 87.4k | 5m17s | 0 | 0 | 22 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 76 | od_1778817290812 | terminated | 155.9k | 3.0k | 1.0k | 2m07s | 0 | 0 | 8 | 1 | 15 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 77 | nt_1778817428031 | terminated | 72.7k | 1.4k | 14.5k | 1m18s | 0 | 0 | 5 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 78 | ed_1778817514469 | terminated | 243.6k | 3.2k | 13.8k | 1m58s | 0 | 0 | 15 | 2 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 79 | ll_1778817645322 | terminated | 437.1k | 4.4k | 68.7k | 9m29s | 0 | 0 | 18 | 10 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 80 | ir_1778818223386 | completed | 30.5k | 202 | '- | 14s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 81 | er_1778818248301 | terminated | 405.9k | 5.6k | 104.2k | 4m03s | 0 | 0 | 20 | 5 | 5 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 82 | rl_1778818499518 | completed | 334.2k | 6.0k | 166 | 3m24s | 0 | 0 | 16 | 17 | 17 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 83 | ls_1778818714450 | completed | 423.6k | 8.3k | 63.6k | 6m56s | 0 | 0 | 22 | 53 | 83 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 84 | rs_1778819145096 | terminated | 316.7k | 4.3k | 22.3k | 3m32s | 0 | 0 | 14 | 54 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 85 | ss_1778819363252 | completed | 384.1k | 2.6k | 51.1k | 2m25s | 0 | 0 | 19 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 86 | ed_1778819522332 | completed | 130.2k | 2.6k | 160 | 1m44s | 0 | 0 | 7 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 87 | ip_1778819636166 | terminated | 108.3k | 761 | 7.4k | 38s | 0 | 0 | 7 | 19 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 88 | ds_1778819680835 | completed | 282.3k | 3.4k | 20.0k | 1m56s | 0 | 0 | 15 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 89 | us_1778819807183 | completed | 358.0k | 5.6k | 21.9k | 3m48s | 0 | 0 | 19 | 10 | 10 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 90 | oc_1778820043732 | completed | 82.0k | 4.3k | '- | 36s | 0 | 0 | 5 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 91 | rl_1778820090369 | completed | 170.9k | 2.6k | 12.7k | 1m49s | 0 | 0 | 8 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 92 | ts_1778820210670 | terminated | 239.1k | 4.6k | 576 | 3m25s | 0 | 0 | 13 | 3 | 2 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 93 | ls_1778820420470 | completed | 104.9k | 793 | 24.4k | 1m05s | 0 | 0 | 5 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 94 | nt_1778820495665 | completed | 637.0k | 4.2k | 15.4k | 4m44s | 0 | 0 | 25 | 47 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 95 | ls_1778820791488 | completed | 61.5k | 654 | 5.8k | 23s | 0 | 0 | 4 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 96 | ta_1778820825788 | terminated | 498.0k | 15.0k | 6.7k | 9m48s | 0 | 0 | 25 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 97 | on_1778821426519 | terminated | 378.7k | 7.6k | 70.2k | 6m26s | 0 | 0 | 21 | 11 | 11 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 98 | se_1778821823795 | terminated | 494.1k | 71.4k | 15.3k | 34m58s | 0 | 0 | 22 | 4 | 4 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 99 | te_1778823934994 | terminated | 391.6k | 1.6k | 98.8k | 4m06s | 0 | 0 | 21 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 100 | ms_1778824430033 | terminated | 78.5k | 954 | 14.0k | 1m56s | 0 | 0 | 5 | 26 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| Summary |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Failed | 82 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Timed out | 11 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Success rate | 7% |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

### Run 10: openrouter/free S1 lazy RefactorBench
Source: `refbench_lazy_openrouter_free_s1.csv` | Rows: 104 | Columns: 18
  Run ID,benchmark_pipeline_20260514_223318 | Status,completed | Model,openrouter/free | Datasets,refbench

| # | Task | Status | Input | Output | Cache | Time | Evals | Cmpct | Reqs | +Lines | -Lines | Files | Model | Build/Test | Model mismatch | Result | Checks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | rs_1778798007746 | completed | 110.8k | 1.7k | 15.1k | 51s | 0 | 0 | 7 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 2 | ed_1778798073671 | completed | 544.1k | 7.8k | 36.7k | 4m29s | 0 | 0 | 24 | 3 | 2 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 3 | at_1778798351380 | completed | 97.1k | 702 | 7.0k | 27s | 0 | 0 | 6 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 4 | ta_1778798389364 | completed | 417.9k | 6.9k | 7.6k | 2m59s | 0 | 0 | 20 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 5 | er_1778798589760 | completed | 601.8k | 5.8k | 61.4k | 3m23s | 0 | 0 | 20 | 5 | 5 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 6 | ns_1778798800573 | terminated | 669.6k | 9.0k | 137.0k | 4m45s | 0 | 0 | 34 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 7 | on_1778799099262 | completed | 282.8k | 3.7k | 30.5k | 1m42s | 0 | 0 | 15 | 41 | 31 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 8 | ic_1778799214874 | completed | 273.8k | 3.0k | 6.0k | 2m49s | 0 | 0 | 13 | 78 | 2 | 1 | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 9 | ue_1778799397600 | terminated | 1.4M | 14.2k | 86.0k | 7m32s | 0 | 0 | 36 | 3 | 3 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 10 | se_1778799863876 | completed | 14.9k | 4 | '- | 3s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 11 | rt_1778799881987 | terminated | 167.7k | 2.6k | 12.3k | 1m25s | 0 | 0 | 11 | 4 | 4 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 12 | hm_1778799975689 | completed | 170.5k | 1.6k | 20.2k | 2m14s | 0 | 0 | 8 | 3 | 3 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 13 | at_1778800121102 | completed | 91.6k | 676 | 17.2k | 24s | 0 | 0 | 6 | 3 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 14 | ls_1778800156002 | completed | 357.5k | 9.2k | 40.5k | 3m16s | 0 | 0 | 18 | 13 | 10 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 15 | ry_1778800361562 | terminated | 518.9k | 7.2k | 23.3k | 3m49s | 0 | 0 | 23 | 4 | 4 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 16 | sk_1778800597496 | completed | 394.5k | 3.4k | 2.0k | 5m52s | 0 | 0 | 18 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 17 | on_1778800959440 | completed | 471.4k | 14.4k | 688 | 5m09s | 0 | 0 | 21 | 12 | 7 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 18 | ze_1778801278191 | completed | 61.6k | 1.4k | 43 | 34s | 0 | 0 | 4 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 19 | on_1778801322417 | completed | 207.4k | 9.1k | 24.3k | 5m04s | 0 | 0 | 8 | 1 | 5 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 20 | ls_1778801635493 | completed | 292.9k | 8.3k | 7.6k | 3m12s | 0 | 0 | 16 | 14 | 6 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 21 | up_1778801836346 | terminated | 30.4k | 375 | '- | 12s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 22 | at_1778801858279 | completed | 159.4k | 6.3k | 16.1k | 1m52s | 0 | 0 | 9 | 5 | 5 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 23 | xt_1778801979802 | completed | 689.2k | 8.8k | 110.0k | 7m53s | 0 | 0 | 31 | 9 | 9 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 24 | re_1778803086762 | completed | 339.3k | 2.8k | 66.3k | 2m30s | 0 | 0 | 18 | 12 | 2 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 25 | er_1778803262394 | completed | 630.8k | 3.9k | 72.9k | 6m43s | 0 | 0 | 29 | 5 | 5 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 26 | er_1778803922401 | terminated | 792.9k | 11.7k | 110.6k | 6m37s | 0 | 0 | 38 | 7 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 27 | ng_1778804520446 | terminated | 320.4k | 4.1k | 52.3k | 3m16s | 0 | 0 | 18 | 17 | 11 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 28 | at_1778804727082 | completed | 435.3k | 10.0k | 35.2k | 7m07s | 0 | 0 | 21 | 86 | 87 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 29 | at_1778805169914 | completed | 184.4k | 4.3k | 16.4k | 3m19s | 0 | 0 | 12 | 33 | 12 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 30 | ss_1778805385345 | terminated | 255.7k | 3.8k | 608 | 2m19s | 0 | 0 | 13 | '- | '- | '- | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 31 | on_1778805696314 | completed | 97.3k | 9.8k | 43 | 1m46s | 0 | 0 | 6 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 32 | ss_1778805818201 | completed | 256.1k | 5.2k | 13.3k | 3m28s | 0 | 0 | 12 | 54 | 7 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 33 | ss_1778806838594 | terminated | 1.3M | 9.1k | 95.9k | 10m04s | 0 | 0 | 42 | 18 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 34 | ss_1778807462076 | completed | 195.8k | 6.9k | 18.1k | 4m01s | 0 | 0 | 10 | 33 | 31 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 35 | de_1778807714519 | completed | 526.5k | 5.5k | 39.7k | 2m53s | 0 | 0 | 25 | 43 | 36 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 36 | se_1778807906263 | completed | 576.2k | 15.5k | 79.2k | 7m01s | 0 | 0 | 35 | 11 | 4 | 2 | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 37 | le_1778808347948 | completed | 186.8k | 2.5k | 24.7k | 1m34s | 0 | 0 | 10 | 43 | 1 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 38 | ls_1778808457465 | completed | 575.5k | 19.9k | 59.7k | 6m14s | 0 | 0 | 28 | 15 | 10 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 39 | ts_1778808850618 | completed | 202.4k | 4.0k | 21.9k | 2m09s | 0 | 0 | 12 | 3 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 40 | fe_1778808997030 | terminated | 167.1k | 1.7k | 528 | 1m08s | 0 | 0 | 9 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 41 | ls_1778809079128 | completed | 177.0k | 6.7k | 19.5k | 2m55s | 0 | 0 | 11 | 25 | 16 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 42 | '-path_1778809270 | completed | 294.8k | 4.6k | 491 | 2m15s | 0 | 0 | 18 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 43 | rs_1778809417476 | completed | 191.2k | 9.9k | 160 | 12m30s | 0 | 0 | 12 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 44 | am_1778810179788 | completed | 128.7k | 1.1k | 384 | 58s | 0 | 0 | 7 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 45 | ls_1778810249892 | terminated | 340.9k | 7.8k | 38.0k | 3m03s | 0 | 0 | 19 | 6 | 6 | 6 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 46 | am_1778810441210 | completed | 870.5k | 7.8k | 102.6k | 7m04s | 0 | 0 | 33 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 47 | ce_1778810882164 | completed | 194.9k | 2.5k | 32.2k | 2m11s | 0 | 0 | 13 | 3 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 48 | ag_1778811026349 | completed | 272.5k | 3.6k | 41.3k | 3m03s | 0 | 0 | 15 | 3 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 49 | es_1778811219869 | completed | 344.2k | 4.4k | 7.6k | 2m46s | 0 | 0 | 20 | 3 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 50 | py_1778811395266 | completed | 344.2k | 4.4k | 7.6k | 2m46s | 0 | 0 | 20 | 3 | 1 | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 51 | ry_1778811397562 | terminated | 64.1k | 562 | 448 | 18s | 0 | 0 | 4 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 52 | tr_1778811666822 | terminated | 452.4k | 8.8k | 28.7k | 5m56s | 0 | 0 | 21 | 6 | 6 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 53 | tr_1778812029118 | completed | 474.2k | 7.4k | 72.2k | 4m13s | 0 | 0 | 26 | 4 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 54 | ders_17788122901 | completed | 412.4k | 5.6k | 33.6k | 3m50s | 0 | 0 | 25 | 4 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 55 | es_1778812532428 | terminated | 250.7k | 3.3k | 1.7k | 2m32s | 0 | 0 | 15 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 56 | xy_1778812695064 | terminated | 372.8k | 2.4k | 47.0k | 1m39s | 0 | 0 | 19 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 57 | ey_1778813050824 | terminated | 267.8k | 2.5k | 60.1k | 2m37s | 0 | 0 | 16 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 58 | ls_1778813215406 | completed | 215.8k | 2.1k | 17.5k | 1m34s | 0 | 0 | 12 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 59 | ns_1778813868681 | terminated | 546.5k | 12.3k | 20.2k | 10m20s | 0 | 0 | 26 | 37 | 4 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 60 | ss_1778814496738 | terminated | 93.1k | 859 | 14.5k | 1m11s | 0 | 0 | 6 | 33 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 61 | up_1778814573585 | completed | 203.5k | 1.9k | 18.6k | 1m42s | 0 | 0 | 11 | 4 | 4 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 62 | en_1778814685929 | completed | 159.3k | 1.9k | 16.9k | 1m45s | 0 | 0 | 9 | 2 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 63 | ns_1778814801764 | terminated | 273.2k | 5.0k | 25.5k | 3m02s | 0 | 0 | 15 | 8 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 64 | ry_1778814990601 | terminated | 307.5k | 3.2k | 28.6k | 1m25s | 0 | 0 | 15 | 9 | 6 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 65 | ns_1778815089795 | completed | 136.2k | 8.6k | 6.2k | 2m24s | 0 | 0 | 8 | 27 | 9 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 66 | ff_1778815246706 | completed | 169.6k | 702 | 7.1k | 49s | 0 | 0 | 9 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 67 | te_1778815308272 | completed | 287.4k | 2.2k | 67.5k | 1m44s | 0 | 0 | 14 | 4 | 4 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 68 | rt_1778815426542 | terminated | 444.0k | 3.9k | 67.4k | 3m15s | 0 | 0 | 22 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 69 | il_1778815636699 | completed | 301.3k | 4.3k | 49.2k | 2m59s | 0 | 0 | 16 | 3 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 70 | il_1778815831407 | terminated | 330.2k | 2.4k | 19.2k | 3m54s | 0 | 0 | 19 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 71 | od_1778816080247 | completed | 210.8k | 4.9k | 6.7k | 3m10s | 0 | 0 | 11 | 15 | 197 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 72 | il_1778816284674 | completed | 158.7k | 3.4k | 528 | 1m22s | 0 | 0 | 10 | 4 | 4 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 73 | ws_1778816375002 | completed | 438.7k | 18.2k | 12.3k | 5m44s | 0 | 0 | 21 | '- | '- | '- | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 74 | ic_1778816740283 | completed | 472.4k | 7.2k | 48.4k | 3m24s | 0 | 0 | 25 | 3 | 3 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 75 | il_1778816955291 | completed | 513.7k | 14.9k | 87.4k | 5m17s | 0 | 0 | 22 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 76 | od_1778817290812 | terminated | 155.9k | 3.0k | 1.0k | 2m07s | 0 | 0 | 8 | 1 | 15 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 77 | nt_1778817428031 | terminated | 72.7k | 1.4k | 14.5k | 1m18s | 0 | 0 | 5 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 78 | ed_1778817514469 | terminated | 243.6k | 3.2k | 13.8k | 1m58s | 0 | 0 | 15 | 2 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 79 | ll_1778817645322 | terminated | 437.1k | 4.4k | 68.7k | 9m29s | 0 | 0 | 18 | 10 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 80 | ir_1778818223386 | completed | 30.5k | 202 | '- | 14s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 81 | er_1778818248301 | terminated | 405.9k | 5.6k | 104.2k | 4m03s | 0 | 0 | 20 | 5 | 5 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |
| 82 | rl_1778818499518 | completed | 334.2k | 6.0k | 166 | 3m24s | 0 | 0 | 16 | 17 | 17 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 83 | ls_1778818714450 | completed | 423.6k | 8.3k | 63.6k | 6m56s | 0 | 0 | 22 | 53 | 83 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 84 | rs_1778819145096 | terminated | 316.7k | 4.3k | 22.3k | 3m32s | 0 | 0 | 14 | 54 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 85 | ss_1778819363252 | completed | 384.1k | 2.6k | 51.1k | 2m25s | 0 | 0 | 19 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 86 | ed_1778819522332 | completed | 130.2k | 2.6k | 160 | 1m44s | 0 | 0 | 7 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 87 | ip_1778819636166 | terminated | 108.3k | 761 | 7.4k | 38s | 0 | 0 | 7 | 19 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 88 | ds_1778819680835 | completed | 282.3k | 3.4k | 20.0k | 1m56s | 0 | 0 | 15 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 89 | us_1778819807183 | completed | 358.0k | 5.6k | 21.9k | 3m48s | 0 | 0 | 19 | 10 | 10 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 90 | oc_1778820043732 | completed | 82.0k | 4.3k | '- | 36s | 0 | 0 | 5 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 91 | rl_1778820090369 | completed | 170.9k | 2.6k | 12.7k | 1m49s | 0 | 0 | 8 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 92 | ts_1778820210670 | terminated | 239.1k | 4.6k | 576 | 3m25s | 0 | 0 | 13 | 3 | 2 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 93 | ls_1778820420470 | completed | 104.9k | 793 | 24.4k | 1m05s | 0 | 0 | 5 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 94 | nt_1778820495665 | completed | 637.0k | 4.2k | 15.4k | 4m44s | 0 | 0 | 25 | 47 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 95 | ls_1778820791488 | completed | 61.5k | 654 | 5.8k | 23s | 0 | 0 | 4 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no |
| 96 | ta_1778820825788 | terminated | 498.0k | 15.0k | 6.7k | 9m48s | 0 | 0 | 25 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 97 | on_1778821426519 | terminated | 378.7k | 7.6k | 70.2k | 6m26s | 0 | 0 | 21 | 11 | 11 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 98 | se_1778821823795 | terminated | 494.1k | 71.4k | 15.3k | 34m58s | 0 | 0 | 22 | 4 | 4 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no |
| 99 | te_1778823934994 | terminated | 391.6k | 1.6k | 98.8k | 4m06s | 0 | 0 | 21 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| 100 | ms_1778824430033 | terminated | 78.5k | 954 | 14.0k | 1m56s | 0 | 0 | 5 | 26 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no |
| Summary |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Failed | 82 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Timed out | 11 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Success rate | 7% |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

### Run 11: minimax-m3 S1 RefactorBench
Source: `benchmark_pipeline_20260611_180455_monitor_exact_export_20260612162020.csv` | Rows: 105 | Columns: 20
  Run ID,benchmark_pipeline_20260611_180455 | Status,failed | Model,minimax/minimax-m3 | Datasets,refbench

| # | Task | Status | Input | Output | Cache | Time | Evals | Cmpct | Reqs | +Lines | -Lines | Files | Model | Build/Test | Model mismatch | Result | Checks | Reason | Build Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | add-log-parameter-get-group-vars | completed | 271.3k | 2.4k | 248.9k | 58s | 0 | 0 | 15 | 8 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 2 | add-log-parameter-is-systemd-managed | completed | 394.0k | 3.9k | 368.9k | 1m43s | 0 | 0 | 22 | 6 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 3 | combine-namespace-compat | completed | 1.7M | 11.7k | 1.6M | 4m42s | 0 | 0 | 52 | 79 | 58 | 6 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 4 | data-to-inventory-data | completed | 189.8k | 1.6k | 158.2k | 50s | 0 | 0 | 10 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 5 | move-quoting-splitter | completed | 288.1k | 5.4k | 259.4k | 1m36s | 0 | 0 | 13 | 17 | 7 | 7 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 6 | new-inventory-patterns | completed | 402.8k | 5.0k | 354.4k | 1m41s | 0 | 0 | 21 | 104 | 77 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 7 | new-utils-class-connection | completed | 674.0k | 5.7k | 638.5k | 2m28s | 0 | 0 | 30 | 53 | 50 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 8 | new-utils-from-basic | completed | 1.8M | 9.4k | 1.7M | 4m25s | 0 | 0 | 66 | 109 | 90 | 13 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 9 | parse_key_value | completed | 1.2M | 7.1k | 1.1M | 3m44s | 0 | 0 | 49 | 32 | 32 | 12 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 10 | rename-lenient-lowercase | completed | 195.9k | 2.3k | 174.4k | 53s | 0 | 0 | 11 | 9 | 9 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 11 | sort-groups-to-group-sort | completed | 233.9k | 1.7k | 211.4k | 56s | 0 | 0 | 14 | 4 | 4 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 12 | add-log-parameter-get-digest-algorithm | completed | 141.5k | 931 | 121.6k | 34s | 0 | 0 | 9 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 13 | add-log-parameter-node-format | terminated | 280.1k | 6.8k | 231.1k | 2m20s | 0 | 0 | 15 | 6 | 5 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 14 | annotation-utils | completed | 240.7k | 3.1k | 220.5k | 1m09s | 0 | 0 | 14 | 12 | 7 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 15 | autoretry-to-retry | completed | 313.0k | 3.6k | 281.3k | 1m27s | 0 | 0 | 16 | 10 | 10 | 6 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 16 | combine-unpickle-task | completed | 211.8k | 2.8k | 180.8k | 59s | 0 | 0 | 12 | 6 | 10 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 17 | dump-message-to-serialization | completed | 292.4k | 2.5k | 237.7k | 1m10s | 0 | 0 | 14 | 10 | 9 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 18 | ensure_serialize | completed | 125.0k | 2.6k | 102.1k | 47s | 0 | 0 | 7 | 9 | 9 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 19 | evaluate-promises-to-serialization | completed | 628.0k | 3.8k | 596.0k | 1m47s | 0 | 0 | 27 | 10 | 9 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 20 | expand-router-string-to-utils | completed | 307.4k | 2.4k | 279.8k | 1m08s | 0 | 0 | 15 | 11 | 9 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 21 | object-mro-lookup | completed | 161.7k | 1.5k | 137.4k | 45s | 0 | 0 | 10 | 2 | 1 | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 22 | rename-host-format | completed | 412.8k | 2.5k | 370.4k | 1m15s | 0 | 0 | 20 | 9 | 9 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 23 | truncate-text | completed | 602.6k | 4.0k | 546.0k | 2m00s | 0 | 0 | 25 | 19 | 17 | 7 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 24 | add-log-parameter-constant-time-compare | completed | 761.4k | 4.5k | 693.9k | 2m20s | 0 | 0 | 32 | 25 | 15 | 7 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 25 | add-log-parameter-get-resolver | completed | 2.7M | 28.1k | 2.6M | 9m21s | 0 | 0 | 62 | 58 | 53 | 11 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 26 | add-log-parameter-resolve-error-handler | completed | 163.1k | 2.0k | 138.2k | 52s | 0 | 0 | 10 | 6 | 6 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 27 | add-none-handling-duration-string | completed | 132.7k | 1.6k | 112.7k | 37s | 0 | 0 | 8 | 5 | '- | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 28 | combine-utils-dates-dateformat | completed | 659.4k | 7.2k | 590.4k | 2m35s | 0 | 0 | 28 | 81 | 12 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 29 | combine-utils-hashable-itercompat | completed | 422.2k | 7.6k | 390.8k | 2m18s | 0 | 0 | 19 | 103 | 10 | 12 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 30 | new-converter-to-python-class | completed | 459.3k | 6.5k | 396.9k | 2m10s | 0 | 0 | 19 | 55 | '- | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 31 | new-path-traversal-exception | completed | 818.3k | 6.0k | 776.2k | 2m19s | 0 | 0 | 30 | 21 | 14 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 32 | new-reference-context-field-class | completed | 851.7k | 6.7k | 807.6k | 2m34s | 0 | 0 | 31 | 79 | 6 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 33 | new-reference-context-graph-class | completed | 1.7M | 10.9k | 1.6M | 4m22s | 0 | 0 | 50 | 34 | 6 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 34 | new-timezone-class | completed | 401.8k | 5.2k | 369.8k | 2m01s | 0 | 0 | 21 | 48 | 36 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 35 | new-utils-adapt-method-mode | completed | 441.3k | 3.8k | 415.0k | 1m37s | 0 | 0 | 21 | 44 | 37 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 36 | new-utils-check-response | completed | 328.2k | 3.4k | 277.5k | 1m14s | 0 | 0 | 16 | 35 | 31 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 37 | new-utils-path-from-module | completed | 552.2k | 7.7k | 496.9k | 2m48s | 0 | 0 | 25 | 36 | 30 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 38 | remove-core-cache-utils | completed | 418.3k | 3.2k | 397.9k | 1m34s | 0 | 0 | 23 | 16 | 4 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 39 | remove-db-models-constants | completed | 1.3M | 15.2k | 1.3M | 5m58s | 0 | 0 | 58 | 28 | 20 | 20 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 40 | rename-file-move-safe | completed | 647.7k | 3.7k | 582.3k | 1m42s | 0 | 0 | 25 | 19 | 18 | 5 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 41 | split-parse-apps-and-model-labels | completed | 503.5k | 3.1k | 449.1k | 1m27s | 0 | 0 | 23 | 25 | 20 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 42 | add-log-parameter-generate-option-id-for-path | completed | 146.6k | 1.5k | 124.5k | 42s | 0 | 0 | 9 | 4 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 43 | exception-handlers-to-handlers | completed | 213.3k | 2.1k | 194.7k | 53s | 0 | 0 | 13 | 8 | 8 | 8 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 44 | get-auth-scheme-param | terminated | 611.3k | 4.3k | 584.0k | 1m51s | 0 | 0 | 27 | 9 | 9 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 45 | openapi-get-utils | completed | 391.1k | 6.5k | 334.3k | 2m02s | 0 | 0 | 19 | 7 | 7 | 7 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 46 | params-to-param | completed | 603.2k | 6.8k | 562.1k | 2m28s | 0 | 0 | 21 | 11 | 11 | 8 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 47 | value-is-a-sequence | completed | 136.7k | 1.3k | 117.4k | 35s | 0 | 0 | 9 | 3 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 48 | add-log-parameter-get-debug-flag | completed | 179.4k | 2.4k | 155.0k | 52s | 0 | 0 | 11 | 6 | 5 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 49 | add-log-parameter-get-flashed-messages | completed | 237.2k | 2.9k | 210.5k | 1m02s | 0 | 0 | 13 | 12 | 7 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 50 | debughelpers-to-helpers.py | completed | 2.7M | 28.1k | 2.6M | 9m21s | 0 | 0 | 62 | 58 | 53 | 11 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 51 | rename-send-from-directory | completed | 237.6k | 4.2k | 210.0k | 1m37s | 0 | 0 | 12 | 7 | 7 | 5 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 52 | render-template-str | completed | 266.7k | 2.7k | 247.9k | 1m10s | 0 | 0 | 16 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 53 | stream-template-str | completed | 224.4k | 1.6k | 198.7k | 52s | 0 | 0 | 13 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 54 | add-log-parameter-get-encoding-from-headers | completed | 159.3k | 1.8k | 137.7k | 45s | 0 | 0 | 10 | 4 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 55 | add-log-parameter-resolve-proxies | completed | 272.6k | 1.9k | 250.8k | 1m03s | 0 | 0 | 17 | 4 | 3 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 56 | add-log-parameter-select-proxy | completed | 298.4k | 1.4k | 274.9k | 1m00s | 0 | 0 | 18 | 5 | 4 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 57 | combine-from-key-to-key | completed | 426.0k | 3.5k | 378.9k | 1m33s | 0 | 0 | 22 | 19 | 35 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 58 | combine-internal-utils-utils | completed | 2.0M | 19.9k | 1.9M | 6m41s | 0 | 0 | 68 | 104 | 67 | 6 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 59 | move-hooks-sessions | completed | 860.4k | 7.1k | 795.0k | 3m14s | 0 | 0 | 35 | 29 | 7 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 60 | new-cookie-utils-class | completed | 1.2M | 6.9k | 1.2M | 3m16s | 0 | 0 | 46 | 77 | 5 | 7 | yes | checked | no | PASSED | code=no build=yes ast=- verified=yes |  |  |
| 61 | rename-lookup-dict-dict-lookup | completed | 166.8k | 2.6k | 137.6k | 53s | 0 | 0 | 9 | 7 | 7 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 62 | rename-super-len-complex-len | completed | 443.7k | 3.8k | 413.0k | 1m32s | 0 | 0 | 22 | 29 | 29 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 63 | split-warnings-exceptions | terminated | 4.7M | 27.7k | 4.6M | 11m45s | 0 | 0 | 122 | 39 | 36 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 64 | py_1781208268625 | completed | 5.1M | 19.7k | 4.9M | 8m35s | 0 | 0 | 104 | 328 | 290 | 15 | no | '- | no | '- |  |  |  |
| 65 | add-log-parameter-delete-directory | completed | 157.6k | 1.5k | 134.4k | 43s | 0 | 0 | 10 | 4 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 66 | add-log-parameter-get-capability-definitions | completed | 229.3k | 1.6k | 207.7k | 1m12s | 0 | 0 | 13 | 5 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 67 | add-log-parameter-recursive-diff | completed | 2.0M | 16.9k | 1.9M | 6m31s | 0 | 0 | 52 | 32 | 12 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 68 | cant-create | completed | 390.4k | 2.3k | 364.2k | 1m22s | 0 | 0 | 22 | 4 | 4 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 69 | channel-to-transport | completed | 311.9k | 2.1k | 292.2k | 1m05s | 0 | 0 | 18 | 3 | 3 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 70 | ex-pillar-fail | completed | 122.6k | 1.1k | 105.4k | 31s | 0 | 0 | 8 | 1 | 1 | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 71 | ex-state-fail | completed | 392.9k | 2.2k | 373.7k | 1m22s | 0 | 0 | 23 | 4 | 4 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 72 | exactly-n-boto-mod | completed | 392.9k | 2.2k | 373.7k | 1m22s | 0 | 0 | 23 | 4 | 4 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 73 | get-unavail | terminated | 113.7k | 1.3k | 95.0k | 30s | 0 | 0 | 7 | 4 | 4 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 74 | iam-to-aws | terminated | 264.4k | 2.0k | 211.7k | 57s | 0 | 0 | 13 | 35 | '- | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 75 | mksls-to-specific | completed | 291.2k | 1.9k | 267.6k | 1m07s | 0 | 0 | 16 | 3 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 76 | namecheap-xmlutil | completed | 1.3M | 10.0k | 1.2M | 3m47s | 0 | 0 | 39 | 82 | 80 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 77 | paged-call-boto-mod | completed | 363.5k | 3.5k | 343.6k | 1m34s | 0 | 0 | 21 | 2 | 13 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 78 | pem-fingerprint | completed | 174.8k | 7.3k | 149.7k | 2m15s | 0 | 0 | 10 | '- | '- | '- | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 79 | perm-denied | completed | 115.5k | 1.8k | 95.7k | 40s | 0 | 0 | 7 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 80 | add-log-parameter-disconnect-all | completed | 115.7k | 1.4k | 95.2k | 33s | 0 | 0 | 7 | 8 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 81 | add-log-parameter-job-dir | completed | 283.0k | 2.2k | 264.2k | 1m04s | 0 | 0 | 17 | 10 | 4 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 82 | add-log-parameter-xmliter | terminated | 570.5k | 16.5k | 515.1k | 9m36s | 0 | 0 | 26 | 9 | 7 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 83 | genspider-functions-to-utils-url | completed | 321.1k | 3.3k | 298.2k | 1m30s | 0 | 0 | 17 | 33 | 29 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 84 | new-downloadermiddlewares-utils | completed | 325.1k | 3.9k | 294.3k | 1m28s | 0 | 0 | 14 | 31 | 20 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 85 | new-spider-utils-in-spiders | completed | 870.9k | 8.0k | 827.2k | 3m10s | 0 | 0 | 32 | 84 | 61 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 86 | new-verify-reactor-class | completed | 950.1k | 7.8k | 886.3k | 3m26s | 0 | 0 | 40 | 34 | 33 | 6 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 87 | not-supported-exception-to-unsupported | completed | 197.4k | 3.4k | 170.7k | 1m12s | 0 | 0 | 10 | 16 | 16 | 6 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 88 | parameterize-gunzip | completed | 874.8k | 7.0k | 839.5k | 2m50s | 0 | 0 | 34 | 23 | 16 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 89 | rename-description-commands | completed | 1.4M | 6.9k | 1.3M | 3m11s | 0 | 0 | 47 | 27 | 27 | 17 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 90 | rename-engine-status | completed | 498.6k | 3.2k | 477.5k | 1m48s | 0 | 0 | 27 | 16 | 16 | 6 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 91 | rename-processtest-testproc | completed | 129.1k | 2.1k | 103.8k | 46s | 0 | 0 | 8 | 9 | 9 | 5 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 92 | sitemap-url-to-url | completed | 765.9k | 7.2k | 704.9k | 2m35s | 0 | 0 | 33 | 23 | 20 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 93 | global-objects | completed | 445.7k | 5.0k | 422.8k | 1m49s | 0 | 0 | 23 | 54 | 27 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 94 | log-utils | completed | 555.4k | 5.3k | 521.0k | 2m24s | 0 | 0 | 24 | 162 | 134 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 95 | option-parser-with-pretty-print | terminated | 987.2k | 10.1k | 948.3k | 3m46s | 0 | 0 | 34 | 56 | 56 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 96 | options-utils | terminated | 10.1M | 56.4k | 9.9M | 20m54s | 0 | 0 | 165 | 832 | 51 | 29 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 97 | remove-locale-data | terminated | 194.8k | 3.1k | 171.2k | 1m05s | 0 | 0 | 11 | 65 | 2 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 98 | rename-http1connection | terminated | 163.5k | 4.3k | 137.5k | 1m22s | 0 | 0 | 9 | 12 | 12 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 99 | rename-to-camel-case | completed | 363.3k | 5.6k | 309.3k | 1m55s | 0 | 0 | 16 | 8 | 8 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 100 | resolvers-as-separate | completed | 363.3k | 5.6k | 309.3k | 1m55s | 0 | 0 | 16 | 8 | 8 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 101 | ms_1781217841000 | completed | 5.1M | 19.7k | 4.9M | 8m35s | 0 | 0 | 104 | 328 | 290 | 15 | no | '- | no | '- |  |  |  |
| Summary |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Failed | 27 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Timed out | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Success rate | 72% |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

### Run 12: kimi-k2.6 S1 RefactorBench 
Source: `benchmark_pipeline_20260612_000413_monitor_exact_export_20260612160703.csv` | Rows: 105 | Columns: 20
  Run ID,benchmark_pipeline_20260612_000413 | Status,completed | Model,moonshotai/kimi-k2.6 | Datasets,refbench

| # | Task | Status | Input | Output | Cache | Time | Evals | Cmpct | Reqs | +Lines | -Lines | Files | Model | Build/Test | Model mismatch | Result | Checks | Reason | Build Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | new-path-traversal-exception | terminated | 686.6k | 26.7k | 231.2k | 20m22s | 0 | 0 | 22 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 2 | add-log-parameter-get-group-vars | completed | 1.1M | 7.6k | 565.3k | 8m11s | 0 | 0 | 42 | '- | '- | '- | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 3 | add-log-parameter-is-systemd-managed | completed | 1.1M | 7.6k | 565.3k | 8m11s | 0 | 0 | 42 | '- | '- | '- | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 4 | combine-namespace-compat | completed | 1.0M | 11.7k | 422.4k | 11m14s | 0 | 0 | 38 | 4 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 5 | data-to-inventory-data | completed | 545.3k | 5.0k | 155.3k | 3m49s | 0 | 0 | 20 | 29 | 28 | 7 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 6 | move-quoting-splitter | completed | 139.1k | 1.4k | 48.2k | 1m53s | 0 | 0 | 9 | 8 | 2 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 7 | new-inventory-patterns | completed | 742.7k | 8.4k | 292.8k | 8m06s | 0 | 0 | 33 | 1 | 1 | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 8 | new-utils-class-connection | completed | 394.5k | 5.3k | 137.2k | 3m03s | 0 | 0 | 18 | 110 | 74 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 9 | new-utils-from-basic | terminated | 880.1k | 15.7k | 351.6k | 15m33s | 0 | 0 | 35 | '- | '- | '- | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 10 | parse_key_value | completed | 2.1M | 18.7k | 1.1M | 19m37s | 0 | 0 | 59 | 114 | 92 | 13 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 11 | rename-lenient-lowercase | completed | 565.3k | 7.9k | 357.5k | 3m05s | 0 | 0 | 14 | 31 | 28 | 10 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 12 | sort-groups-to-group-sort | completed | 737.6k | 5.4k | 172.4k | 7m15s | 0 | 0 | 32 | '- | '- | '- | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 13 | add-log-parameter-get-digest-algorithm | completed | 191.5k | 3.4k | 29.7k | 4m36s | 0 | 0 | 12 | 8 | 4 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 14 | add-log-parameter-node-format | completed | 158.1k | 1.6k | 16.0k | 2m12s | 0 | 0 | 10 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 15 | annotation-utils | completed | 1.3M | 17.2k | 519.2k | 17m37s | 0 | 0 | 47 | 5 | 5 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 16 | autoretry-to-retry | terminated | 485.5k | 16.8k | 42.6k | 14m06s | 0 | 0 | 24 | 13 | 7 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 17 | combine-unpickle-task | completed | 716.6k | 10.8k | 320.9k | 11m27s | 0 | 0 | 34 | 12 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 18 | dump-message-to-serialization | terminated | 467.9k | 4.1k | 204.7k | 5m17s | 0 | 0 | 26 | 6 | 10 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 19 | ensure_serialize | completed | 184.9k | 3.4k | 95.8k | 3m09s | 0 | 0 | 9 | 10 | 7 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 20 | evaluate-promises-to-serialization | completed | 510.8k | 3.8k | 242.7k | 4m25s | 0 | 0 | 23 | 9 | 10 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 21 | expand-router-string-to-utils | terminated | 1.0M | 15.8k | 176.7k | 14m49s | 0 | 0 | 28 | 11 | 7 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 22 | object-mro-lookup | completed | 301.1k | 2.5k | 56.0k | 2m01s | 0 | 0 | 14 | 10 | 10 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 23 | rename-host-format | completed | 138.1k | 1.1k | 57.2k | 44s | 0 | 0 | 9 | 2 | 1 | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 24 | truncate-text | completed | 840.3k | 7.7k | 435.1k | 7m58s | 0 | 0 | 32 | 5 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 25 | add-log-parameter-constant-time-compare | terminated | 723.1k | 6.9k | 490.3k | 5m05s | 0 | 0 | 27 | 13 | 9 | 7 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 26 | add-log-parameter-get-resolver | completed | 1.9M | 10.9k | 893.3k | 10m59s | 0 | 0 | 57 | 15 | 14 | 7 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 27 | add-log-parameter-resolve-error-handler | completed | 1.4M | 8.9k | 588.6k | 8m56s | 0 | 0 | 36 | 27 | 27 | 11 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 28 | add-none-handling-duration-string | completed | 104.1k | 1.3k | 6.5k | 51s | 0 | 0 | 6 | 6 | 6 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 29 | combine-utils-dates-dateformat | completed | 150.5k | 2.0k | 87.9k | 1m39s | 0 | 0 | 8 | 5 | '- | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 30 | combine-utils-hashable-itercompat | completed | 273.9k | 5.3k | 121.6k | 4m09s | 0 | 0 | 14 | 78 | 11 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 31 | new-converter-to-python-class | completed | 567.4k | 11.5k | 217.1k | 10m00s | 0 | 0 | 31 | 95 | '- | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 32 | new-reference-context-field-class | terminated | 1.1M | 25.0k | 285.1k | 22m13s | 0 | 0 | 42 | 26 | '- | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 33 | new-reference-context-graph-class | completed | 2.8M | 28.1k | 1.4M | 17m13s | 0 | 0 | 64 | 232 | 89 | 5 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 34 | new-timezone-class | completed | 533.1k | 8.8k | 106.3k | 6m00s | 0 | 0 | 26 | 47 | 36 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 35 | new-utils-adapt-method-mode | terminated | 234.0k | 6.8k | 28.4k | 6m29s | 0 | 0 | 11 | 46 | 39 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 36 | new-utils-check-response | completed | 345.5k | 5.0k | 113.0k | 2m42s | 0 | 0 | 17 | 35 | 31 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 37 | new-utils-path-from-module | terminated | 180.2k | 6.0k | 31.9k | 2m13s | 0 | 0 | 10 | 35 | 27 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 38 | remove-core-cache-utils | completed | 189.2k | 2.5k | 74.6k | 1m13s | 0 | 0 | 11 | 17 | 5 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 39 | remove-db-models-constants | completed | 1.5M | 15.8k | 446.0k | 14m51s | 0 | 0 | 60 | 11 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 40 | rename-file-move-safe | completed | 413.3k | 5.2k | 160.0k | 4m19s | 0 | 0 | 15 | 21 | 19 | 5 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 41 | split-parse-apps-and-model-labels | completed | 170.4k | 2.7k | 32.8k | 2m05s | 0 | 0 | 9 | 29 | 18 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 42 | add-log-parameter-generate-option-id-for-path | completed | 662.7k | 3.8k | 282.1k | 4m54s | 0 | 0 | 31 | 2 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 43 | exception-handlers-to-handlers | terminated | 692.5k | 5.5k | 290.1k | 5m58s | 0 | 0 | 30 | 12 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 44 | get-auth-scheme-param | completed | 830.2k | 6.9k | 210.4k | 7m34s | 0 | 0 | 38 | 11 | 5 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 45 | openapi-get-utils | completed | 621.5k | 7.5k | 293.3k | 7m06s | 0 | 0 | 29 | 21 | 7 | 8 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 46 | params-to-param | terminated | 686.3k | 12.3k | 257.4k | 11m07s | 0 | 0 | 29 | 14 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 47 | value-is-a-sequence | terminated | 638.8k | 4.2k | 250.8k | 5m25s | 0 | 0 | 36 | 6 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 48 | add-log-parameter-get-debug-flag | completed | 147.9k | 2.9k | '- | 2m10s | 0 | 0 | 8 | 12 | 6 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 49 | add-log-parameter-get-flashed-messages | completed | 855.6k | 7.1k | 268.2k | 8m17s | 0 | 0 | 43 | 15 | 7 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 50 | debughelpers-to-helpers.py | completed | 855.6k | 7.1k | 268.2k | 8m17s | 0 | 0 | 43 | 15 | 7 | 2 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 51 | rename-send-from-directory | terminated | 381.0k | 8.4k | 92.4k | 8m14s | 0 | 0 | 19 | 6 | 3 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 52 | render-template-str | terminated | 334.6k | 12.0k | 53.0k | 11m26s | 0 | 0 | 12 | '- | '- | '- | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 53 | stream-template-str | terminated | 305.1k | 3.4k | 76.1k | 4m34s | 0 | 0 | 19 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 54 | add-log-parameter-get-encoding-from-headers | completed | 361.8k | 3.5k | 148.7k | 3m29s | 0 | 0 | 22 | 5 | 4 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 55 | add-log-parameter-resolve-proxies | completed | 372.5k | 3.2k | 144.7k | 4m46s | 0 | 0 | 20 | 3 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 56 | add-log-parameter-select-proxy | completed | 165.9k | 1.8k | 42.6k | 2m25s | 0 | 0 | 10 | 5 | 4 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 57 | combine-from-key-to-key | terminated | 343.8k | 6.5k | 129.1k | 5m38s | 0 | 0 | 17 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 58 | combine-internal-utils-utils | terminated | 1.6M | 26.3k | 492.6k | 24m10s | 0 | 0 | 58 | 145 | 7 | 3 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 59 | move-hooks-sessions | completed | 1.3M | 17.0k | 529.5k | 16m08s | 0 | 0 | 57 | 24 | 1 | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 60 | new-cookie-utils-class | completed | 598.2k | 37.5k | 118.3k | 18m17s | 0 | 0 | 20 | 168 | 153 | 7 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 61 | rename-lookup-dict-dict-lookup | completed | 244.3k | 2.4k | 99.7k | 1m58s | 0 | 0 | 14 | 9 | 6 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 62 | rename-super-len-complex-len | completed | 476.0k | 6.8k | 81.1k | 6m05s | 0 | 0 | 22 | 1 | 1 | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 63 | split-warnings-exceptions | terminated | 1.6M | 38.2k | 639.7k | 23m54s | 0 | 0 | 55 | 27 | 17 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 64 | add-log-parameter-delete-directory | completed | 364.1k | 6.2k | 64.4k | 4m16s | 0 | 0 | 16 | 9 | 6 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 65 | add-log-parameter-get-capability-definitions | terminated | 356.5k | 10.6k | 105.9k | 5m34s | 0 | 0 | 19 | 9 | 5 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 66 | add-log-parameter-recursive-diff | completed | 454.2k | 8.7k | 116.4k | 7m30s | 0 | 0 | 15 | 9 | 4 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 67 | cant-create | terminated | 100.7k | 1.7k | 32.0k | 2m18s | 0 | 0 | 6 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 68 | channel-to-transport | terminated | 373.2k | 7.1k | 98.7k | 4m26s | 0 | 0 | 21 | 8 | 3 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 69 | ex-pillar-fail | completed | 199.8k | 1.1k | 103.4k | 1m28s | 0 | 0 | 12 | '- | '- | '- | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 70 | ex-state-fail | terminated | 27.2k | 172 | '- | 9s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 71 | exactly-n-boto-mod | terminated | 341.3k | 25.2k | 64.7k | 23m50s | 0 | 0 | 17 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 72 | get-unavail | completed | 338.9k | 2.1k | 103.5k | 4m05s | 0 | 0 | 15 | 4 | 4 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 73 | iam-to-aws | completed | 231.3k | 3.1k | 48.4k | 3m33s | 0 | 0 | 11 | 35 | '- | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 74 | mksls-to-specific | completed | 448.7k | 6.7k | 37.2k | 9m16s | 0 | 0 | 25 | 3 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 75 | namecheap-xmlutil | terminated | 1.2M | 17.3k | 152.8k | 23m49s | 0 | 0 | 48 | 75 | 77 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 76 | paged-call-boto-mod | completed | 135.6k | 3.9k | '- | 4m10s | 0 | 0 | 7 | 3 | 13 | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 77 | pem-fingerprint | completed | 950.0k | 12.2k | 114.2k | 14m30s | 0 | 0 | 34 | 10 | 6 | 6 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 78 | perm-denied | completed | 102.4k | 1.3k | 27.8k | 3m08s | 0 | 0 | 7 | 3 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 79 | add-log-parameter-disconnect-all | terminated | 153.7k | 1.6k | 66.9k | 1m54s | 0 | 0 | 9 | 5 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 80 | py_1781248429973 | completed | 1.4M | 20.9k | 561.0k | 24m13s | 0 | 0 | 35 | 12 | 277 | 1 | no | '- | no | '- |  |  |  |
| 81 | add-log-parameter-job-dir | terminated | 153.7k | 1.6k | 66.9k | 1m54s | 0 | 0 | 9 | 5 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 82 | add-log-parameter-xmliter | terminated | 992.7k | 7.6k | 855.7k | 7m32s | 0 | 0 | 39 | 30 | 27 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 83 | genspider-functions-to-utils-url | completed | 201.0k | 2.2k | 147.5k | 1m23s | 0 | 0 | 10 | 29 | 29 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 84 | new-downloadermiddlewares-utils | completed | 201.5k | 2.1k | 172.0k | 1m28s | 0 | 0 | 12 | 27 | 20 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 85 | new-spider-utils-in-spiders | terminated | 231.2k | 2.6k | 194.6k | 1m47s | 0 | 0 | 10 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 86 | new-verify-reactor-class | terminated | 197.4k | 5.6k | 32.3k | 10m13s | 0 | 0 | 11 | 62 | 13 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 87 | not-supported-exception-to-unsupported | terminated | 1.4M | 6.1k | 1.1M | 4m46s | 0 | 0 | 39 | 16 | 16 | 6 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 88 | parameterize-gunzip | terminated | 685.7k | 5.2k | 630.8k | 2m44s | 0 | 0 | 28 | 23 | 16 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 89 | rename-description-commands | terminated | 175.7k | 7.2k | 122.9k | 3m55s | 0 | 0 | 7 | 27 | 27 | 17 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 90 | rename-engine-status | terminated | 127.1k | 3.0k | 102.4k | 1m23s | 0 | 0 | 7 | 22 | 17 | 7 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 91 | rename-processtest-testproc | terminated | 106.3k | 1.8k | 75.8k | 1m23s | 0 | 0 | 7 | 9 | 9 | 5 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 92 | sitemap-url-to-url | terminated | 246.9k | 1.9k | 205.0k | 1m20s | 0 | 0 | 11 | 19 | 14 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 93 | global-objects | terminated | 580.5k | 6.0k | 365.8k | 4m49s | 0 | 0 | 22 | 43 | 28 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 94 | log-utils | terminated | 999.8k | 11.0k | 747.4k | 9m49s | 0 | 0 | 34 | 175 | 147 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 95 | option-parser-with-pretty-print | terminated | 2.3M | 18.6k | 1.9M | 10m01s | 0 | 0 | 59 | 57 | 60 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 96 | options-utils | terminated | 2.0M | 15.6k | 1.9M | 6m15s | 0 | 0 | 65 | 138 | 41 | 25 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 97 | remove-locale-data | terminated | 117.6k | 2.7k | 100.4k | 1m39s | 0 | 0 | 7 | 64 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 98 | rename-http1connection | terminated | 557.5k | 5.4k | 489.5k | 3m10s | 0 | 0 | 26 | 17 | 17 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 99 | rename-to-camel-case | terminated | 298.0k | 2.7k | 223.1k | 2m26s | 0 | 0 | 15 | 8 | 8 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 100 | resolvers-as-separate | terminated | 1.4M | 20.9k | 561.0k | 24m13s | 0 | 0 | 35 | 12 | 277 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 101 | tcpclient-connect-params | terminated | 951.7k | 13.1k | 738.3k | 8m35s | 0 | 0 | 34 | 50 | 13 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| Summary |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Failed | 21 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Timed out | 8 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Success rate | 71% |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

### Run 13: deepseek-v4-pro S3 RefactorBench
Source: `benchmark_pipeline_20260616_052828_monitor_exact_export_20260616074053.csv` | Rows: 23 | Columns: 20
  Run ID,benchmark_pipeline_20260616_052828 | Status,completed | Model,deepseek/deepseek-v4-pro | Datasets,refbench

| # | Task | Status | Input | Output | Cache | Time | Evals | Cmpct | Reqs | +Lines | -Lines | Files | Model | Build/Test | Model mismatch | Result | Checks | Reason | Build Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | new-utils-from-basic | terminated | 963.0k | 24.6k | 645.6k | 9m27s | 0 | 0 | 43 | 110 | 92 | 13 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 2 | annotation-utils | terminated | 387.4k | 10.0k | 256.0k | 4m08s | 0 | 0 | 25 | 12 | 7 | 3 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 3 | combine-unpickle-task | terminated | 488.1k | 9.9k | 79.5k | 3m38s | 0 | 0 | 29 | 6 | 10 | 3 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 4 | add-log-parameter-constant-time-compare | terminated | 488.1k | 9.9k | 79.5k | 3m38s | 0 | 0 | 29 | 6 | 10 | 3 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 5 | add-log-parameter-get-resolver | terminated | 677.8k | 18.8k | 494.0k | 5m48s | 0 | 0 | 28 | 21 | 15 | 7 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 6 | add-log-parameter-resolve-error-handler | terminated | 328.0k | 11.2k | 12.7k | 7m29s | 0 | 0 | 21 | 11 | 6 | 4 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 7 | new-path-traversal-exception | terminated | 1.0M | 20.8k | 354.3k | 9m44s | 0 | 0 | 39 | 26 | 19 | 5 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 8 | debughelpers-to-helpers.py | terminated | 487.3k | 7.5k | 42.4k | 3m50s | 0 | 0 | 33 | 32 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 9 | new-verify-reactor-class | terminated | 912.5k | 30.9k | 207.1k | 9m16s | 0 | 0 | 41 | 54 | 52 | 6 | yes | checked | no | PASSED | code=no build=yes ast=- verified=yes |  |  |
| 10 | parameterize-gunzip | terminated | 668.9k | 13.7k | 160.5k | 4m57s | 0 | 0 | 35 | 22 | 16 | 5 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 11 | global-objects | terminated | 416.5k | 13.5k | 90.1k | 4m38s | 0 | 0 | 23 | 46 | 25 | 4 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 12 | log-utils | terminated | 431.4k | 13.2k | 98.8k | 5m19s | 0 | 0 | 22 | 155 | 131 | 4 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 13 | option-parser-with-pretty-print | terminated | 904.1k | 20.5k | 259.2k | 9m49s | 0 | 0 | 39 | 53 | 55 | 3 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 14 | options-utils | terminated | 1.3M | 26.8k | 821.4k | 9m33s | 0 | 0 | 42 | 145 | 114 | 28 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 15 | remove-locale-data | terminated | 496.4k | 7.8k | 196.5k | 3m52s | 0 | 0 | 23 | 64 | 1 | 1 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 16 | rename-http1connection | terminated | 352.9k | 14.3k | 150.1k | 5m02s | 0 | 0 | 23 | 12 | 12 | 5 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 17 | rename-to-camel-case | terminated | 337.6k | 8.0k | 214.5k | 3m25s | 0 | 0 | 21 | 8 | 8 | 2 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 18 | resolvers-as-separate | terminated | 760.6k | 27.2k | 401.3k | 10m35s | 0 | 0 | 34 | 301 | 277 | 2 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 19 | tcpclient-connect-params | terminated | 747.5k | 17.1k | 404.6k | 9m21s | 0 | 0 | 30 | 80 | 41 | 5 | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| Summary |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Failed | 17 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Timed out | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Success rate | 5% |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

### Run 14: minimax-m3 S1 SWE-Refactor
Source: `minimax_s1_default_swerefactor_revalidated.csv` | Rows: 184 | Columns: 9
  Run ID,benchmark_pipeline_20260612_042658 | Status,revalidated | Model,minimax/minimax-m3 | Datasets,swe-refactor

| # | UniqueId | Project | Type | Status | AST | Compile | Message |
|---|---|---|---|---|---|---|---|
| 1 | 1a6443b724a3539b000bcaa2ed9f8016b6bb4f38_412_453_135_143_474_514 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 2 | 1a6443b724a3539b000bcaa2ed9f8016b6bb4f38_455_481_135_143_516_541 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 3 | 1a6443b724a3539b000bcaa2ed9f8016b6bb4f38_483_559_135_143_543_618 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 4 | 1a6443b724a3539b000bcaa2ed9f8016b6bb4f38_54_77_135_143_54_76 | checkstyle | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 5 | 664227cd5bf9c649847461d8055a7ee573f483e5_99_155_876_886_99_153 | checkstyle | Extract And Move Method | completed | False | False | Extracted method must be public static. |
| 6 | 7a9913aa64f911e41eae958b757e73a5d2f93205_232_247__629_644 | checkstyle | Move And Rename Method | completed | True | False | the Move And Rename Method operation is successful. |
| 7 | ba76f3e4f33194b0a1d687e95a58395bd9590321_240_254_432_439_262_277 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 8 | bfb3e5f5e416211bc95799426edba4581b442d0d_101_117_399_409_101_117 | checkstyle | Extract And Move Method | completed | False | True | the code did not perform Extract And Move Method operation. |
| 9 | bfb3e5f5e416211bc95799426edba4581b442d0d_110_119_399_409_110_122 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 10 | bfb3e5f5e416211bc95799426edba4581b442d0d_112_120_399_409_112_123 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 11 | bfb3e5f5e416211bc95799426edba4581b442d0d_178_195_385_397_178_195 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 12 | bfb3e5f5e416211bc95799426edba4581b442d0d_197_214_385_397_197_214 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 13 | bfb3e5f5e416211bc95799426edba4581b442d0d_204_216_399_409_200_213 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 14 | bfb3e5f5e416211bc95799426edba4581b442d0d_232_240_399_409_232_243 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 15 | bfb3e5f5e416211bc95799426edba4581b442d0d_237_243_399_409_237_243 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 16 | bfb3e5f5e416211bc95799426edba4581b442d0d_241_254_385_397_241_254 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 17 | bfb3e5f5e416211bc95799426edba4581b442d0d_243_254_385_397_243_254 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 18 | bfb3e5f5e416211bc95799426edba4581b442d0d_256_268_385_397_256_268 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 19 | bfb3e5f5e416211bc95799426edba4581b442d0d_261_273_399_409_258_271 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 20 | bfb3e5f5e416211bc95799426edba4581b442d0d_270_282_385_397_270_282 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 21 | bfb3e5f5e416211bc95799426edba4581b442d0d_284_293_385_397_284_293 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 22 | bfb3e5f5e416211bc95799426edba4581b442d0d_295_306_385_397_295_306 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 23 | bfb3e5f5e416211bc95799426edba4581b442d0d_322_345_385_397_322_345 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 24 | bfb3e5f5e416211bc95799426edba4581b442d0d_335_358_399_409_335_358 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 25 | bfb3e5f5e416211bc95799426edba4581b442d0d_336_343_399_409_336_347 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 26 | bfb3e5f5e416211bc95799426edba4581b442d0d_345_352_399_409_349_360 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 27 | bfb3e5f5e416211bc95799426edba4581b442d0d_391_401_399_409_391_405 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 28 | bfb3e5f5e416211bc95799426edba4581b442d0d_431_448_385_397_431_448 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 29 | bfb3e5f5e416211bc95799426edba4581b442d0d_459_473_385_397_459_473 | checkstyle | Extract And Move Method | completed | False | True | the code did not perform Extract And Move Method operation. |
| 30 | bfb3e5f5e416211bc95799426edba4581b442d0d_465_476_399_409_465_477 | checkstyle | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 31 | bfb3e5f5e416211bc95799426edba4581b442d0d_466_494_399_409_466_494 | checkstyle | Extract And Move Method | completed | False | True | the code did not perform Extract And Move Method operation. |
| 32 | bfb3e5f5e416211bc95799426edba4581b442d0d_47_55_385_397_47_55 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 33 | bfb3e5f5e416211bc95799426edba4581b442d0d_490_501_385_397_490_501 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 34 | bfb3e5f5e416211bc95799426edba4581b442d0d_567_581_385_397_567_581 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 35 | bfb3e5f5e416211bc95799426edba4581b442d0d_583_600_385_397_583_600 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 36 | bfb3e5f5e416211bc95799426edba4581b442d0d_602_619_385_397_602_619 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 37 | bfb3e5f5e416211bc95799426edba4581b442d0d_621_630_385_397_621_630 | checkstyle | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 38 | bfb3e5f5e416211bc95799426edba4581b442d0d_68_76_399_409_68_76 | checkstyle | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 39 | bfb3e5f5e416211bc95799426edba4581b442d0d_829_842_385_397_829_842 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 40 | bfb3e5f5e416211bc95799426edba4581b442d0d_82_99_399_409_82_99 | checkstyle | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 41 | bfb3e5f5e416211bc95799426edba4581b442d0d_98_106_399_409_98_106 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 42 | cd8ef61ea62f3155040501fd21e20b37dfc8cd26_95_130_108_146_87_98 | checkstyle | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 43 | e2c6e148a92e01b3c6037b33440ee7006f742793_373_383__372_388_79_87 | checkstyle | Move And Inline Method | completed | False | True | the code did not perform Move And Inline Method operation. |
| 44 | 0d84f279d6dd6486b581acf2ea2ad212530e16fc_126_145_120_126_126_141 | commons-io | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 45 | 7245fbd82735eed3fc5510f8b468b77f1e984fb2_174_198_401_423_522_535 | commons-io | Extract And Move Method | completed | False | False | Extracted method must be public static. |
| 46 | 7566f557c2fa172d7677fcde06514e8a68356f81_189_209_101_108_189_202 | commons-io | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 47 | 8a786abb5e2cc04568517f1f8c053578c3e313a6_40_44_54_63_40_44 | commons-io | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 48 | 8a786abb5e2cc04568517f1f8c053578c3e313a6_40_50_57_67_40_50 | commons-io | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 49 | 8a786abb5e2cc04568517f1f8c053578c3e313a6_42_53_57_67_42_53 | commons-io | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 50 | a8ee7b9defba5ed7c83c1fa06b4020930ea5f00e_185_196_870_883_186_196 | commons-io | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 51 | b3ce147431dbad1bbd2e91d527560d7d4a1b9def_83_105_3315_3324_85_103 | commons-io | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 52 | c1692f43ef5a41328b54bbbcd06285120aff52c3_74_102_709_724_74_101 | commons-io | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 53 | 479532b83db2d7b228e4128f2db02233f91e6e91_7804_7836_1414_1448_7804_7830 | commons-lang | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 54 | cdddb82e12ef7b2cc770125e930bde040b032213_5681_5709_1044_1086_5681_5708 | commons-lang | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 55 | cdddb82e12ef7b2cc770125e930bde040b032213_5872_5905_1044_1086_5871_5906 | commons-lang | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 56 | e4c03c5e38b3e2550da7a1f9084d93dad32386ef_1694_1725_600_634_1694_1719 | commons-lang | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 57 | a9c3d3ac68223c83a98022eb88bbcf0f14a66863_49_55__192_198 | guava | Move And Rename Method | completed | False | False | the code did not perform Move And Rename Method operation. |
| 58 | a9c3d3ac68223c83a98022eb88bbcf0f14a66863_57_73__200_216 | guava | Move And Rename Method | completed | True | False | the Move And Rename Method operation is successful. |
| 59 | a9c3d3ac68223c83a98022eb88bbcf0f14a66863_75_92__218_235 | guava | Move And Rename Method | completed | True | False | the Move And Rename Method operation is successful. |
| 60 | b007d6db4ab71c5fc94623cac6eb8a90e227ff3a_607_637_28_30_608_637 | guava | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 61 | b03067f2c78b2352cba8f5136c9aa0be667068a5_88_93__164_168 | guava | Move And Rename Method | completed | False | False | the code did not perform Move And Rename Method operation. |
| 62 | b03067f2c78b2352cba8f5136c9aa0be667068a5_97_106__185_194 | guava | Move And Rename Method | completed | True | False | the Move And Rename Method operation is successful. |
| 63 | ee9ac70a9296645b3f883773eb950961bb12f0d0_568_584_56_58_570_586 | guava | Extract And Move Method | completed | False | False | Extracted method must be public static. |
| 64 | ee9ac70a9296645b3f883773eb950961bb12f0d0_586_596_60_62_588_598 | guava | Extract And Move Method | timeout | False | False | Invalid target file path: |
| 65 | 26e73937756de5781043f120905b71abe9398e5e_27_49_461_463_27_49 | hibernate-orm | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 66 | 26e73937756de5781043f120905b71abe9398e5e_34_59_461_463_34_59 | hibernate-orm | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 67 | 26e73937756de5781043f120905b71abe9398e5e_38_64_461_463_38_64 | hibernate-orm | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 68 | 26e73937756de5781043f120905b71abe9398e5e_66_91_461_463_66_91 | hibernate-orm | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 69 | 2f7052c0ce5114e492c7dc4e4b8abd5283b2fe13_43_121_50_53_40_94 | hibernate-orm | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 70 | 5dcbdf64f11dfdcf25fd5a4a571f978b5ade2a8e_353_385_638_661_335_353 | hibernate-orm | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 71 | 72e2da2da84fae761f14ceeb822bd3e946690c78_820_877__895_952_231_234 | hibernate-orm | Move And Inline Method | completed | False | False | the code did not perform Move And Inline Method operation. |
| 72 | 96cba56591e3e8c6dabaf35d954bd5911b1471ae_123_224_87_97_128_191 | hibernate-orm | Extract And Move Method | completed | False | True | the code did not perform Extract And Move Method operation. |
| 73 | ba05533a036e73ac119169392b0da49273dc2e5b_330_336_23_28_350_356 | hibernate-orm | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 74 | c04caa18de3c5ff81c17ebb151430b9cf18b6284_109_126_92_95_102_119 | hibernate-orm | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 75 | 05c12b8fd2eb002ad9246efd04d8fa27c9379a4b_23_29_46_53_19_21 | hibernate-search | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/backen |
| 76 | 0b4c69d582f4c29554d78da38daebbc49d9d40da_144_165_75_79_142_162 | hibernate-search | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 77 | 0c6c0d87a14968fd7a417b4943835c7dfadeed0f_78_111__118_152_76_78 | hibernate-search | Move And Inline Method | completed | False | False | the code did not perform Move And Inline Method operation. |
| 78 | 14e6370a9ab5e7fca20e508f6413bd11ed242cde_35_43__215_222 | hibernate-search | Move And Rename Method | completed | False | False | Cannot extract method name from moved method code. |
| 79 | 314cff098d6147b783fa091ce3ebcc54a87522aa_109_114__83_88 | hibernate-search | Move And Rename Method | completed | True | True | the Move And Rename Method operation is successful. |
| 80 | 314cff098d6147b783fa091ce3ebcc54a87522aa_90_95__83_88 | hibernate-search | Move And Rename Method | completed | False | False | the code did not perform Move And Rename Method operation. |
| 81 | 3ba4b03373611f27e258496ad8376ea8dc123642_134_148_201_204_122_129 | hibernate-search | Extract And Move Method | completed | False | False | Extracted method must be public static. |
| 82 | 3ba4b03373611f27e258496ad8376ea8dc123642_51_95_281_284_52_83 | hibernate-search | Extract And Move Method | timeout | False | False | Invalid target file path: |
| 83 | 4809368dec30478582c165d2c01aa254f8bf06ab_116_140_84_96_122_133 | hibernate-search | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 84 | 4c0595551f48dcca939fc3f7d3ea5bcf86dcbe7d_263_274__57_68 | hibernate-search | Move And Rename Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/mapper |
| 85 | 520908200e1e83c994b39a93131741bc114ee85d_321_385_23_32_320_384 | hibernate-search | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/util/i |
| 86 | 60720a3723b836213b0e663b71fcbdbb3ce58d36_79_98__325_344 | hibernate-search | Move And Rename Method | completed | False | False | Refactored code does not call moved method 'getId'. |
| 87 | 64d26592b1ac48943690f7690355d44821591f36_179_185__186_195_57_60 | hibernate-search | Move And Inline Method | completed | False | True | the code did not perform Move And Inline Method operation. |
| 88 | 6b55b85d003d11848939dbdf2640fcb479397186_73_88__93_108 | hibernate-search | Move And Rename Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/docume |
| 89 | 6b65d5b3d028b6cf672822b29edb9610db6adca4_67_70__103_163_228_230 | hibernate-search | Move And Inline Method | completed | False | False | the code did not perform Move And Inline Method operation. |
| 90 | 8233e6e5e455472b841a7a2b0aee22089f1e2b43_114_126_85_87_37_47 | hibernate-search | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 91 | b369ab192fd1c80ab666c63e65224bf90f658292_132_142_214_224_132_139 | hibernate-search | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/mapper |
| 92 | b67c74bdf7a5a1a8102fb0b0179bdc0774366c29_114_152__114_152_17_24 | hibernate-search | Move And Inline Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/integr |
| 93 | b67c74bdf7a5a1a8102fb0b0179bdc0774366c29_117_140__117_140_17_24 | hibernate-search | Move And Inline Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/integr |
| 94 | b67c74bdf7a5a1a8102fb0b0179bdc0774366c29_184_230__184_230_17_24 | hibernate-search | Move And Inline Method | completed | True | False | the Move And Inline Method operation is successful. |
| 95 | b67c74bdf7a5a1a8102fb0b0179bdc0774366c29_198_246__198_246_17_24 | hibernate-search | Move And Inline Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/integr |
| 96 | be929dfca72583e5cef800af2f97727e75184a76_53_128_91_96_53_123 | hibernate-search | Extract And Move Method | timeout | False | False | Invalid target file path: |
| 97 | c1738e3fcb5ac2ded491a9ff1b9aa65e941be327_22_34__29_40 | hibernate-search | Move And Rename Method | completed | False | False | Cannot extract method name from moved method code. |
| 98 | da64c4e549b8dfd9c17e7753247d8028bc022529_57_86_264_266_57_86 | hibernate-search | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 99 | daaa9ff20cae0f7751636f16bcaf0cf2512c16a4_159_190_18_20_158_189 | hibernate-search | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/backen |
| 100 | daaa9ff20cae0f7751636f16bcaf0cf2512c16a4_167_236_16_21_167_236 | hibernate-search | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 101 | daaa9ff20cae0f7751636f16bcaf0cf2512c16a4_40_90_18_20_40_90 | hibernate-search | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/backen |
| 102 | ea4e402fd1d991e8c01ae3918047796dd2f3ab8b_48_51__103_108 | hibernate-search | Move And Rename Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/mapper |
| 103 | f307576b2d1a89c3814067a2b6b62df1d8cd45fb_143_182_80_86_143_182 | hibernate-search | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 104 | f50cbfc772b75e7d7a983359b9baca383bc6ae9f_62_65__81_84 | hibernate-search | Move And Rename Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/hibernate-search/util/i |
| 105 | f6398f46e661b12bb5cd7d429c52bd84f5830f79_86_133_316_337_158_177 | hibernate-search | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 106 | 034b17a06497b52eb066eaf1ece5f086305ec840_72_76_133_135_73_77 | javaparser | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/javaparser/javaparser-c |
| 107 | 2903fc918dd87be53192aa1065047392f7adf4d1_76_98__79_110_156_161 | javaparser | Move And Inline Method | no_response | False | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 108 | 2b503c32229deae7d432f59dab710839ecf76c4c_203_211_25_27_203_211 | javaparser | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 109 | 547da782d2ea7f1abc35e5c1e5852928962a11ef_60_63_178_189_60_63 | javaparser | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/javaparser/javaparser-c |
| 110 | 78d0ea5d493f0ab2e83bb70d7023b670bfa2f7b6_32_49_120_123_29_34 | javaparser | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 111 | 86f41353d40bfd3ef0669b863926626b6c4949bf_622_653_132_135_616_629 | javaparser | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 112 | b08e66263903837d53a688b5d12a758c8cdf167e_87_129_53_55_87_129 | javaparser | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/javaparser/javaparser-c |
| 113 | c378a677ebcd999d853b3e5867ac7ca7cd8e73cb_359_371_187_198_357_360 | javaparser | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 114 | ead1412d06bf2ba7eaec982231023aef4aed370a_88_91__77_80_66_68 | javaparser | Move And Inline Method | completed | False | False | the code did not perform Move And Inline Method operation. |
| 115 | 2a777a84cfdc9ccb79aa906cde80e0f44977d3a7_75_80__81_86 | junit5 | Move And Rename Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/junit5/junit-platform-c |
| 116 | 50b28568a20c85473460504f484ac84b0308dc5d_390_396_576_578_390_396 | junit5 | Extract And Move Method | completed | False | True | the code did not perform Extract And Move Method operation. |
| 117 | 50b28568a20c85473460504f484ac84b0308dc5d_398_404_580_582_398_404 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 118 | 50b28568a20c85473460504f484ac84b0308dc5d_406_412_584_586_406_412 | junit5 | Extract And Move Method | completed | False | True | the code did not perform Extract And Move Method operation. |
| 119 | 50b28568a20c85473460504f484ac84b0308dc5d_429_434_576_578_426_431 | junit5 | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 120 | 50b28568a20c85473460504f484ac84b0308dc5d_436_441_580_582_433_438 | junit5 | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 121 | 50b28568a20c85473460504f484ac84b0308dc5d_443_448_584_586_440_445 | junit5 | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 122 | 50b28568a20c85473460504f484ac84b0308dc5d_472_478_580_582_466_472 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 123 | 50b28568a20c85473460504f484ac84b0308dc5d_480_486_584_586_474_480 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 124 | 50b28568a20c85473460504f484ac84b0308dc5d_488_494_588_590_482_488 | junit5 | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 125 | 50b28568a20c85473460504f484ac84b0308dc5d_503_508_576_578_494_499 | junit5 | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 126 | 50b28568a20c85473460504f484ac84b0308dc5d_510_515_580_582_501_506 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 127 | 50b28568a20c85473460504f484ac84b0308dc5d_517_522_584_586_508_513 | junit5 | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 128 | 50b28568a20c85473460504f484ac84b0308dc5d_524_529_588_590_515_520 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 129 | 50b28568a20c85473460504f484ac84b0308dc5d_538_544_576_578_526_532 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 130 | 50b28568a20c85473460504f484ac84b0308dc5d_546_552_580_582_534_540 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 131 | 50b28568a20c85473460504f484ac84b0308dc5d_554_560_584_586_542_548 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 132 | 50b28568a20c85473460504f484ac84b0308dc5d_562_568_588_590_550_556 | junit5 | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 133 | 50b28568a20c85473460504f484ac84b0308dc5d_61_93_569_574_61_78 | junit5 | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 134 | 9f6ad01b6d4753a0cb8f6c366371b277d49d035b_84_91__23_30 | junit5 | Move And Rename Method | completed | False | False | Cannot extract method name from moved method code. |
| 135 | 50b21cf68b400a29369de58b9286d29e368212a7_16_18_46_49_18_20 | mockito | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 136 | 00d391261d90afb005aac22dd9e1beaccb13766a_99_120_220_224_125_147 | pmd | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 137 | 0276320abf2c66cae14d2ad24e2b2fb0386943b3_63_98__61_95_45_47 | pmd | Move And Inline Method | completed | False | False | the code did not perform Move And Inline Method operation. |
| 138 | 05870c98cc05805d6272d12f5080afad3a14e2b6_1102_1105_154_172_1102_1105 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 139 | 05870c98cc05805d6272d12f5080afad3a14e2b6_16_30_101_111_16_30 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 140 | 05870c98cc05805d6272d12f5080afad3a14e2b6_29_44_101_111_30_45 | pmd | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 141 | 05870c98cc05805d6272d12f5080afad3a14e2b6_60_76_101_111_60_76 | pmd | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 142 | 05870c98cc05805d6272d12f5080afad3a14e2b6_75_99_101_111_76_100 | pmd | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 143 | 05870c98cc05805d6272d12f5080afad3a14e2b6_77_80_101_111_77_80 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 144 | 08b19dbcdde5d6258515cf2620a855e7775d46ef_50_60_183_187_53_63 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 145 | 0fec3640a30bd92e6a2d2a0f31888365edaa36e7_28_31_25_28_28_31 | pmd | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 146 | 1540ec6d9148fc14fc1673f4df1d33030d2ffcf7_13_15__13_15 | pmd | Move And Rename Method | completed | False | False | the code did not perform Move And Rename Method operation. |
| 147 | 20a3c39b4d88b0e5716b9e72880ad91d810d6b04_260_301_103_114_259_293 | pmd | Extract And Move Method | completed | False | False | Invalid target file path: |
| 148 | 2123ab3d5d7dcfc867ada3af119c3d3e9cb6183e_31_41_140_150_23_26 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 149 | 214e80a5f1d68e3b42efeacab5b0fc226202ef05_442_462_100_106_441_461 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 150 | 26bcbd839a79055a0ff037da3c8c54ad2bdfdead_21_27__22_28_65_75 | pmd | Move And Inline Method | completed | False | False | the code did not perform Move And Inline Method operation. |
| 151 | 2995f156caf2b55369ef28108f0b6077e4186eb2_58_81_72_76_43_50 | pmd | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 152 | 396567636fa1dbef2f7766f8c9ef57b4c095773e_40_42_57_59_40_42 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 153 | 5031c83c880d11f215b2b21919ff3091c6f951bf_49_55_100_109_42_47 | pmd | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 154 | 5c36ee1eba5a08732d6fc53b0a69010a279a10de_179_218_123_134_182_221 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 155 | 5dc2774c0a53810717358cc850b69c6e7fe0a463_100_215_237_243_94_149 | pmd | Extract And Move Method | timeout | False | False | Invalid target file path: |
| 156 | 5f2a5bb67813ac5acb38a8bac6d335181d79fd9f_34_37_31_34_34_37 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 157 | 6253b696ea9b04ecf4a0c832473a178ade97f32d_25_30_26_28_25_29 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 158 | 868883819020b0780313358e00f6132b3e8dc73f_215_224__207_216 | pmd | Move And Rename Method | completed | False | False | the code did not perform Move And Rename Method operation. |
| 159 | 91d0ebf4620b9cda44ce6f02232fe8a003d82efd_187_194_20_22_175_180 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 160 | 97c08a37ab6e5f0dc0bc2c38d865207b69b7eb2d_14_20_26_28_14_20 | pmd | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/pmd/pmd-java/src/main/j |
| 161 | 994b8402d59773888977d768d395526acfe5cf16_30_33_63_66_46_49 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 162 | a70e70ad15995e87060380ee241e36c045d44883_33_39_43_46_29_32 | pmd | Extract And Move Method | completed | False | False | the code did not perform Extract And Move Method operation. |
| 163 | a733da4dcfa19b80f21480040aaf701e72e51bb5_103_107__114_118_28_30 | pmd | Move And Inline Method | timeout | False | False | Invalid target file path: ########################## refactored_class_code |
| 164 | bc25e58dfc8b3fe32c173e2cf213bf9e83869ce0_37_51_125_127_46_61 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 165 | cfbb14c91c24b1a50cf4b41cd855fd780375a14f_48_110_81_84_36_59 | pmd | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/pmd/pmd-core/src/main/j |
| 166 | cfbb14c91c24b1a50cf4b41cd855fd780375a14f_48_110_86_92_36_59 | pmd | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/pmd/pmd-core/src/main/j |
| 167 | cfbb14c91c24b1a50cf4b41cd855fd780375a14f_48_110_94_102_36_59 | pmd | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/pmd/pmd-core/src/main/j |
| 168 | da03fafabb2146ca3b2cd3f61484754490dfc9fb_144_160_71_106_142_144 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 169 | e4f5d027b2d86f675208d8da53d0bb4b6365ad20_167_190_56_63_167_190 | pmd | Extract And Move Method | completed | True | False | the Extract And Move Method operation is successful. |
| 170 | ff2f5ef93c1b3150583e9611b2a8fd8159e3aa66_48_50__156_158 | pmd | Move And Rename Method | completed | False | False | the code did not perform Move And Rename Method operation. |
| 171 | ff2f5ef93c1b3150583e9611b2a8fd8159e3aa66_54_56__164_166 | pmd | Move And Rename Method | completed | False | False | the code did not perform Move And Rename Method operation. |
| 172 | 18b3ac1bfe19cbe26650e13d9cb1ad3ec1011a48_87_120_280_295_87_119 | shenyu | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 173 | 2f4ff7f4b7100db14c549f47941fff8c472d875d_157_178_418_425_181_206 | shenyu | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 174 | 9725874eaa20ec87a3d8beea168f3a9ade9ba76d_100_114_114_135_98_104 | shenyu | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/shenyu/shenyu-plugin/sh |
| 175 | d8c7b57eed6c5ab5880cca8f49920e8b4eb30f8d_48_68_156_158_64_103 | shenyu | Extract And Move Method | completed | True | True | the Extract And Move Method operation is successful. |
| 176 | 515688992bec0973288f3deb9b4538dd780c8760_103_165_98_100_103_165 | zxing | Extract And Move Method | completed | False | False | Cannot extract class names from source/target files. |
| 177 | 515688992bec0973288f3deb9b4538dd780c8760_96_205_98_100_96_205 | zxing | Extract And Move Method | completed | False | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/projects/zxing/core/src/main/jav |
| Summary |  |  |  |  |  |  |  |
| AST pass | 97 |  |  |  |  |  |  |
| AST rate | 54.8% |  |  |  |  |  |  |
| Compile pass | 60 |  |  |  |  |  |  |
| Compile rate | 33.9% |  |  |  |  |  |  |
| Both pass | 52 |  |  |  |  |  |  |
| Both rate | 29.4% |  |  |  |  |  |  |

---

### Run 15: deepseek-v4-pro S1-eval SWE-Refactor
Source: `s1_eval_swe_deepseek_never_passed.csv` | Rows: 8 | Columns: 14
  # SWE-Refactor S1-Eval (deepseek/deepseek-v4-pro) | "# 142 never-passed tasks, descriptive mode, eval loop enabled" | # Run: benchmark_pipeline_20260616_052901 | Duration: 5h 16m | # Status: STOPPED - OpenRouter credit exhausted (HTTP 403) after 8/142 tasks

| # | Project | RefactoringId | Passed | Duration(s) | AgentDur(s) | EvalDur(s) | EvalLoops | InputTok | OutputTok | CacheRead | Requests | CodeBLEU | RMResult |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | checkstyle | bfb3e5f5e416_98_106_399_409_98_106 | True | 1153 | 1051 | 102 | 3 | 1409457 | 12581 | 811776 | 39 | 0.363 | Success |
| 2 | checkstyle | bfb3e5f5e416_68_76_399_409_68_76 | True | 534 | 432 | 102 | 2 | 494837 | 6461 | 177152 | 16 | 0.363 | Success |
| 3 | checkstyle | bfb3e5f5e416_101_117_399_409_101_117 | True | 2959 | 2869 | 90 | 8 | 6602983 | 75335 | 4188672 | 97 | 0.915 | Success |
| 4 | checkstyle | bfb3e5f5e416_82_99_399_409_82_99 | True | 8943 | 8834 | 109 | 31 | 10327685 | 165096 | 8090880 | 157 | 0.919 | Success |
| 5 | checkstyle | bfb3e5f5e416_465_476_399_409_465_477 | True | 541 | 433 | 108 | 1 | 621109 | 7987 | 210304 | 21 | 0.398 | Success |
| 6 | checkstyle | bfb3e5f5e416_261_273_399_409_258_271 | True | 583 | 473 | 110 | 1 | 620570 | 16520 | 453888 | 19 | 0.803 | Success |
| 7 | checkstyle | bfb3e5f5e416_204_216_399_409_200_213 | True | 661 | 560 | 101 | 1 | 475804 | 17388 | 320000 | 16 | 0.794 | Success |
| 8 | checkstyle | bfb3e5f5e416_237_243_399_409_237_243 | True | 1132 | 1024 | 108 | 3 | 1136801 | 20611 | 680576 | 28 | 0.817 | Success |

---

### Run 16: gpt-5-mini S1 default SWE-Refactor
Source: `s1_default_results.csv` | Rows: 75 | Columns: 20

| setup | uniqueId | project | refactoringType | result | code | build | ast | verified | codebleu | inputTokens | outputTokens | cacheTokens | time | requests | linesAdded | linesRemoved | filesModified | evalLoops | compactions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s1_default | 1a6443b724a3539b000bcaa2ed9f8016b6bb4f38_412_453_135_143_474_514 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.5958 | 150.9k | 12.6k | 114.9k | 3m37s | 4 | 60 | 0 | 1 |  |  |
| s1_default | 1a6443b724a3539b000bcaa2ed9f8016b6bb4f38_455_481_135_143_516_541 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.5497 | 191.6k | 8.2k | 157.8k | 2m10s | 5 | 41 | 4 | 1 |  |  |
| s1_default | 1a6443b724a3539b000bcaa2ed9f8016b6bb4f38_483_559_135_143_543_618 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.0529 | 156.8k | 9.1k | 120.7k | 2m26s | 4 | 85 | 0 | 1 |  |  |
| s1_default | 1a6443b724a3539b000bcaa2ed9f8016b6bb4f38_54_77_135_143_54_76 | checkstyle | Extract And Move Method | FAILED | Y | Y | N | N | 0.0383 | 121.4k | 7.2k | 100.9k | 2m11s | 5 | 34 | 1 | 1 |  |  |
| s1_default | 664227cd5bf9c649847461d8055a7ee573f483e5_99_155_876_886_99_153 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 122.7k | 5.6k | 96.6k | 1m43s | 4 | 57 | 0 | 1 |  |  |
| s1_default | 7a9913aa64f911e41eae958b757e73a5d2f93205_232_247__629_644 | checkstyle | Move And Rename Method | FAILED | N | N | N | N |  | 209.2k | 7.1k | 185.6k | 2m39s | 8 | 31 | 0 | 1 |  |  |
| s1_default | ba76f3e4f33194b0a1d687e95a58395bd9590321_240_254_432_439_262_277 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.0556 | 73.9k | 4.3k | 53.4k | 1m27s | 3 | 0 | 0 | 0 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_101_117_399_409_101_117 | checkstyle | Extract And Move Method | FAILED | Y | Y | N | N | 0.7117 | 122.2k | 5.0k | 98.3k | 2m10s | 5 | 15 | 1 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_110_119_399_409_110_122 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.2750 | 121.3k | 5.1k | 97.9k | 2m01s | 5 | 18 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_112_120_399_409_112_123 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 91.6k | 4.4k | 72.8k | 1m34s | 4 | 14 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_178_195_385_397_178_195 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.4751 | 133.9k | 6.1k | 109.4k | 2m35s | 5 | 19 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_197_214_385_397_197_214 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.5317 | 152.8k | 5.4k | 105.2k | 1m59s | 6 | 21 | 3 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_204_216_399_409_200_213 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 96.0k | 3.5k | 75.6k | 2m23s | 4 | 18 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_232_240_399_409_232_243 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.4860 | 96.4k | 4.5k | 76.4k | 2m06s | 4 | 12 | 4 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_237_243_399_409_237_243 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.5925 | 114.8k | 7.6k | 86.4k | 3m06s | 4 | 16 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_241_254_385_397_241_254 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.4276 | 83.5k | 7.1k | 59.9k | 2m18s | 3 | 24 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_243_254_385_397_243_254 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 124.4k | 6.6k | 98.8k | 2m01s | 4 | 18 | 3 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_256_268_385_397_256_268 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.0798 | 163.8k | 5.9k | 133.4k | 2m19s | 5 | 21 | 4 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_261_273_399_409_258_271 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 131.9k | 6.1k | 86.1k | 3m56s | 5 | 20 | 3 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_270_282_385_397_270_282 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 193.5k | 7.6k | 161.2k | 2m29s | 6 | 24 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_284_293_385_397_284_293 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1926 | 166.0k | 8.5k | 133.1k | 2m30s | 5 | 18 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_295_306_385_397_295_306 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1852 | 194.8k | 5.9k | 164.4k | 1m55s | 6 | 20 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_322_345_385_397_322_345 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3304 | 162.9k | 5.8k | 132.9k | 1m57s | 5 | 38 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_335_358_399_409_335_358 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 139.9k | 6.9k | 115.3k | 2m26s | 5 | 32 | 3 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_336_343_399_409_336_347 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3011 | 135.1k | 9.1k | 88.4k | 3m17s | 5 | 16 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_345_352_399_409_349_360 | checkstyle | Extract And Move Method | FAILED | Y | Y | N | N | 0.6757 | 205.0k | 14.5k | 169.7k | 5m08s | 6 | 18 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_391_401_399_409_391_405 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.1077 | 107.9k | 7.2k | 87.3k | 2m29s | 4 | 11 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_431_448_385_397_431_448 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.5496 | 81.8k | 5.8k | 58.9k | 1m39s | 3 | 27 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_459_473_385_397_459_473 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3087 | 255.2k | 10.2k | 220.0k | 3m28s | 7 | 22 | 3 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_465_476_399_409_465_477 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.0315 | 328.2k | 9.5k | 300.5k | 3m40s | 11 | 23 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_466_494_399_409_466_494 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 150.9k | 6.2k | 122.9k | 2m43s | 5 | 41 | 1 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_47_55_385_397_47_55 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3547 | 165.0k | 6.7k | 139.4k | 3m11s | 6 | 13 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_490_501_385_397_490_501 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1625 | 227.0k | 6.5k | 164.9k | 3m01s | 7 | 22 | 3 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_567_581_385_397_567_581 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 166.6k | 7.4k | 136.4k | 2m52s | 5 | 24 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_583_600_385_397_583_600 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 164.5k | 5.5k | 130.3k | 2m21s | 5 | 28 | 3 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_602_619_385_397_602_619 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1365 | 160.0k | 6.6k | 128.1k | 2m00s | 5 | 29 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_621_630_385_397_621_630 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.2846 | 165.4k | 8.2k | 133.1k | 2m19s | 5 | 21 | 0 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_68_76_399_409_68_76 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 145.5k | 6.8k | 125.3k | 5m42s | 5 | 14 | 1 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_829_842_385_397_829_842 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1584 | 134.7k | 6.0k | 104.3k | 2m12s | 4 | 24 | 2 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_82_99_399_409_82_99 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 175.2k | 5.7k | 155.3k | 2m37s | 7 | 31 | 3 | 1 |  |  |
| s1_default | bfb3e5f5e416211bc95799426edba4581b442d0d_98_106_399_409_98_106 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3674 | 93.3k | 4.3k | 50.8k | 1m23s | 4 | 14 | 1 | 1 |  |  |
| s1_default | cd8ef61ea62f3155040501fd21e20b37dfc8cd26_95_130_108_146_87_98 | checkstyle | Extract And Move Method | FAILED | Y | N | N | N | 0.3861 | 111.1k | 6.7k | 91.3k | 2m07s | 5 | 34 | 2 | 1 |  |  |
| s1_default | e2c6e148a92e01b3c6037b33440ee7006f742793_373_383__372_388_79_87 | checkstyle | Move And Inline Method | FAILED | N | N | N | N |  | 265.2k | 10.5k | 231.6k | 2m44s | 9 | 496 | 0 | 1 |  |  |
| s1_default | 0d84f279d6dd6486b581acf2ea2ad212530e16fc_126_145_120_126_126_141 | commons-io | Extract And Move Method | FAILED | Y | N | N | N | 0.1610 | 112.2k | 4.9k | 96.3k | 1m27s | 6 | 13 | 2 | 1 |  |  |
| s1_default | 7245fbd82735eed3fc5510f8b468b77f1e984fb2_174_198_401_423_522_535 | commons-io | Extract And Move Method | FAILED | Y | N | N | N | 0.1714 | 100.7k | 5.6k | 84.1k | 1m42s | 5 | 22 | 3 | 1 |  |  |
| s1_default | 7566f557c2fa172d7677fcde06514e8a68356f81_189_209_101_108_189_202 | commons-io | Extract And Move Method | FAILED | Y | N | N | N | 0.0880 | 76.6k | 4.4k | 60.4k | 1m23s | 4 | 22 | 6 | 1 |  |  |
| s1_default | 8a786abb5e2cc04568517f1f8c053578c3e313a6_40_44_54_63_40_44 | commons-io | Extract And Move Method | FAILED | N | N | N | N |  | 140.8k | 6.0k | 124.5k | 2m00s | 7 | 12 | 3 | 1 |  |  |
| s1_default | 8a786abb5e2cc04568517f1f8c053578c3e313a6_40_50_57_67_40_50 | commons-io | Extract And Move Method | FAILED | N | N | N | N |  | 92.8k | 6.2k | 75.8k | 2m08s | 5 | 16 | 2 | 1 |  |  |
| s1_default | 8a786abb5e2cc04568517f1f8c053578c3e313a6_42_53_57_67_42_53 | commons-io | Extract And Move Method | FAILED | Y | N | N | N | 0.5072 | 85.6k | 4.9k | 57.5k | 1m33s | 5 | 17 | 2 | 1 |  |  |
| s1_default | a8ee7b9defba5ed7c83c1fa06b4020930ea5f00e_185_196_870_883_186_196 | commons-io | Extract And Move Method | FAILED | N | N | N | N |  | 142.8k | 4.1k | 124.8k | 1m26s | 7 | 9 | 0 | 1 |  |  |
| s1_default | b3ce147431dbad1bbd2e91d527560d7d4a1b9def_83_105_3315_3324_85_103 | commons-io | Extract And Move Method | FAILED | N | N | N | N |  | 118.7k | 7.4k | 82.4k | 2m25s | 6 | 36 | 0 | 1 |  |  |
| s1_default | c1692f43ef5a41328b54bbbcd06285120aff52c3_74_102_709_724_74_101 | commons-io | Extract And Move Method | FAILED | Y | N | N | N | 0.1506 | 86.9k | 7.9k | 67.8k | 2m32s | 4 | 33 | 1 | 1 |  |  |
| s1_default | 479532b83db2d7b228e4128f2db02233f91e6e91_7804_7836_1414_1448_7804_7830 | commons-lang | Extract And Move Method | TIMEOUT | N | N | N | N |  | 112.2k | 4.9k | 96.3k | 1m27s | 6 | 13 | 2 | 1 |  |  |
| s1_default | cdddb82e12ef7b2cc770125e930bde040b032213_5681_5709_1044_1086_5681_5708 | commons-lang | Extract And Move Method | TIMEOUT | N | N | N | N |  | 112.2k | 4.9k | 96.3k | 1m27s | 6 | 13 | 2 | 1 |  |  |
| s1_default | cdddb82e12ef7b2cc770125e930bde040b032213_5872_5905_1044_1086_5871_5906 | commons-lang | Extract And Move Method | TIMEOUT | N | N | N | N |  | 112.2k | 4.9k | 96.3k | 1m27s | 6 | 13 | 2 | 1 |  |  |
| s1_default | e4c03c5e38b3e2550da7a1f9084d93dad32386ef_1694_1725_600_634_1694_1719 | commons-lang | Extract And Move Method | TIMEOUT | N | N | N | N |  | 112.2k | 4.9k | 96.3k | 1m27s | 6 | 13 | 2 | 1 |  |  |
| s1_default | a9c3d3ac68223c83a98022eb88bbcf0f14a66863_49_55__192_198 | guava | Move And Rename Method | FAILED | Y | N | N | N | 0.3257 | 191.5k | 6.4k | 166.8k | 2m10s | 7 | 11 | 2 | 1 |  |  |
| s1_default | a9c3d3ac68223c83a98022eb88bbcf0f14a66863_57_73__200_216 | guava | Move And Rename Method | FAILED | Y | N | N | N | 0.6233 | 101.6k | 7.4k | 81.2k | 1m50s | 4 | 26 | 1 | 1 |  |  |
| s1_default | a9c3d3ac68223c83a98022eb88bbcf0f14a66863_75_92__218_235 | guava | Move And Rename Method | FAILED | Y | N | N | N | 0.3299 | 191.9k | 8.2k | 168.8k | 3m18s | 7 | 25 | 0 | 1 |  |  |
| s1_default | b007d6db4ab71c5fc94623cac6eb8a90e227ff3a_607_637_28_30_608_637 | guava | Extract And Move Method | FAILED | Y | N | N | N | 0.2750 | 196.9k | 7.2k | 166.1k | 2m33s | 6 | 31 | 1 | 1 |  |  |
| s1_default | b03067f2c78b2352cba8f5136c9aa0be667068a5_88_93__164_168 | guava | Move And Rename Method | FAILED | Y | N | N | N | 0.3559 | 182.1k | 7.2k | 137.3k | 2m30s | 7 | 102 | 1 | 1 |  |  |
| s1_default | b03067f2c78b2352cba8f5136c9aa0be667068a5_97_106__185_194 | guava | Move And Rename Method | FAILED | N | N | N | N |  | 298.0k | 9.7k | 269.1k | 3m49s | 10 | 110 | 3 | 1 |  |  |
| s1_default | ee9ac70a9296645b3f883773eb950961bb12f0d0_568_584_56_58_570_586 | guava | Extract And Move Method | FAILED | Y | N | N | N | 0.0980 | 233.5k | 6.0k | 173.7k | 2m28s | 7 | 22 | 2 | 1 |  |  |
| s1_default | ee9ac70a9296645b3f883773eb950961bb12f0d0_586_596_60_62_588_598 | guava | Extract And Move Method | FAILED | Y | N | N | N | 0.3701 | 199.4k | 5.9k | 166.4k | 1m48s | 6 | 19 | 3 | 1 |  |  |
| s1_default | 26e73937756de5781043f120905b71abe9398e5e_27_49_461_463_27_49 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 |  |  |
| s1_default | 26e73937756de5781043f120905b71abe9398e5e_34_59_461_463_34_59 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 |  |  |
| s1_default | 26e73937756de5781043f120905b71abe9398e5e_38_64_461_463_38_64 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 |  |  |
| s1_default | 26e73937756de5781043f120905b71abe9398e5e_66_91_461_463_66_91 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 |  |  |
| s1_default | 2f7052c0ce5114e492c7dc4e4b8abd5283b2fe13_43_121_50_53_40_94 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 |  |  |
| s1_default | 5dcbdf64f11dfdcf25fd5a4a571f978b5ade2a8e_353_385_638_661_335_353 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 |  |  |
| s1_default | 72e2da2da84fae761f14ceeb822bd3e946690c78_820_877__895_952_231_234 | hibernate-orm | Move And Inline Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 | 1 |  |
| s1_default | 96cba56591e3e8c6dabaf35d954bd5911b1471ae_123_224_87_97_128_191 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 |  |  |
| s1_default | ba05533a036e73ac119169392b0da49273dc2e5b_330_336_23_28_350_356 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  | 199.8k | 7.3k | 173.1k | 2m33s | 6 | 32 | 0 | 1 | 1 |  |
| s1_default | c04caa18de3c5ff81c17ebb151430b9cf18b6284_109_126_92_95_102_119 | hibernate-orm | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  | 0 | 0 | 0 | 0 | 1 |  |
| s1_default | b67c74bdf7a5a1a8102fb0b0179bdc0774366c29_184_230__184_230_17_24 | hibernate-search | Move And Inline Method | FAILED | Y | N | N | N | 0.7118 |  |  |  |  | 0 | 0 | 0 | 0 |  |  |

---

### Run 17: gpt-5-mini S1-eval SWE-Refactor
Source: `s1_eval_results.csv` | Rows: 33 | Columns: 20

| setup | uniqueId | project | refactoringType | result | code | build | ast | verified | codebleu | inputTokens | outputTokens | cacheTokens | time | requests | linesAdded | linesRemoved | filesModified | evalLoops | compactions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_101_117_399_409_101_117 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.0896 | 2.3M | 32.3k | 2.3M | 21m57s | 42 | 60 | 21 | 1 | 5 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_110_119_399_409_110_122 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.5674 | 192.3k | 6.4k | 168.3k | 2m30s | 7 | 17 | 3 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_112_120_399_409_112_123 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.4631 | 196.9k | 5.3k | 175.9k | 2m53s | 8 | 13 | 3 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_178_195_385_397_178_195 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.6651 | 154.5k | 4.9k | 134.3k | 1m44s | 6 | 16 | 1 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_197_214_385_397_197_214 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.2052 | 198.6k | 7.4k | 173.2k | 3m10s | 7 | 34 | 0 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_204_216_399_409_200_213 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.6918 | 208.9k | 6.6k | 182.9k | 2m30s | 7 | 20 | 1 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_232_240_399_409_232_243 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.5555 | 468.1k | 10.1k | 435.3k | 3m36s | 14 | 25 | 12 | 1 | 2 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_237_243_399_409_237_243 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3713 | 562.6k | 11.5k | 527.5k | 5m06s | 16 | 25 | 12 | 1 | 3 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_241_254_385_397_241_254 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.4163 | 282.3k | 7.4k | 258.3k | 4m14s | 10 | 23 | 3 | 1 | 2 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_261_273_399_409_258_271 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3234 | 153.9k | 4.3k | 132.6k | 2m18s | 6 | 19 | 2 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_270_282_385_397_270_282 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1045 | 242.2k | 6.6k | 178.9k | 2m15s | 7 | 22 | 2 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_284_293_385_397_284_293 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.0617 | 359.5k | 6.7k | 263.0k | 2m31s | 10 | 15 | 4 | 1 | 2 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_295_306_385_397_295_306 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1446 | 232.4k | 5.5k | 137.3k | 1m53s | 7 | 22 | 2 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_322_345_385_397_322_345 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.4016 |  |  |  |  | 0 | 0 | 0 | 0 |  |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_335_358_399_409_335_358 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 174.6k | 7.1k | 151.0k | 2m25s | 6 | 30 | 5 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_336_343_399_409_336_347 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.2256 | 283.0k | 6.5k | 256.3k | 3m10s | 9 | 20 | 4 | 1 | 2 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_345_352_399_409_349_360 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3001 | 182.0k | 7.7k | 102.0k | 2m32s | 6 | 17 | 2 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_391_401_399_409_391_405 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 290.1k | 8.7k | 261.1k | 3m09s | 9 | 20 | 6 | 1 | 2 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_431_448_385_397_431_448 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1601 | 6.0M | 50.2k | 5.9M | 21m16s | 94 | 52 | 62 | 1 | 12 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_459_473_385_397_459_473 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3169 | 233.5k | 5.6k | 203.1k | 1m47s | 7 | 22 | 2 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_465_476_399_409_465_477 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.5586 | 338.0k | 8.9k | 313.3k | 4m27s | 11 | 19 | 5 | 1 | 2 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_466_494_399_409_466_494 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 157.7k | 8.7k | 133.6k | 3m08s | 5 | 39 | 1 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_47_55_385_397_47_55 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3547 | 179.8k | 4.6k | 156.3k | 1m25s | 7 | 14 | 2 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_490_501_385_397_490_501 | checkstyle | Extract And Move Method | FAILED | N | N | N | N |  | 290.9k | 9.1k | 255.5k | 3m09s | 8 | 18 | 2 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_567_581_385_397_567_581 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3178 | 184.5k | 7.9k | 152.8k | 2m37s | 5 | 25 | 2 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_583_600_385_397_583_600 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1246 | 318.0k | 7.1k | 285.7k | 3m00s | 9 | 34 | 3 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_602_619_385_397_602_619 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.1426 | 199.8k | 7.3k | 173.1k | 2m33s | 6 | 32 | 0 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_621_630_385_397_621_630 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.2846 | 256.4k | 5.5k | 198.7k | 2m45s | 8 | 16 | 3 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_68_76_399_409_68_76 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 1.0000 | 624.7k | 11.9k | 596.6k | 6m31s | 19 | 18 | 3 | 1 | 3 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_829_842_385_397_829_842 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.2228 | 12.2M | 100.6k | 11.7M | 40m49s | 180 | 48 | 33 | 1 | 16 | 2 |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_82_99_399_409_82_99 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.0857 | 187.7k | 4.5k | 137.5k | 1m47s | 7 | 17 | 1 | 1 | 1 |  |
| s1_eval | bfb3e5f5e416211bc95799426edba4581b442d0d_98_106_399_409_98_106 | checkstyle | Extract And Move Method | PASSED | Y | Y | Y | Y | 0.3625 | 189.8k | 4.7k | 183.6k | 1m33s | 7 | 17 | 2 | 1 | 1 |  |
| s1_eval | 50b21cf68b400a29369de58b9286d29e368212a7_16_18_46_49_18_20 | mockito | Extract And Move Method | TIMEOUT | N | N | N | N |  |  |  |  |  |  |  |  |  |  |  |

---

### Run 18: openrouter/free S1 SWE-Refactor
Source: `benchmark_pipeline_20260514_223325_monitor_exact_export_20260515085613.csv` | Rows: 130 | Columns: 18
  Run ID,benchmark_pipeline_20260514_223325 | Status,completed | Model,openrouter/free | Datasets,swe

| # | Task | Status | Input | Output | Cache | Time | Evals | Cmpct | Reqs | +Lines | -Lines | Files | Model | Build/Test | Model mismatch | Result | Checks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 02dd8194f0 | terminated | 324.8k | 10.1k | 73.1k | 4m22s | 0 | 0 | 16 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 2 | 85c422b256 | terminated | 797.4k | 9.5k | 84.5k | 3m54s | 0 | 0 | 19 | 26 | 1 | 2 | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 3 | bb1ca321af | terminated | 196.8k | 3.6k | '- | 1m17s | 0 | 0 | 7 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 4 | 05da82dbad | terminated | 362.1k | 8.3k | 9.1k | 3m13s | 0 | 0 | 14 | 12 | 3 | 1 | yes | present | no | PASSED | code=no build=yes ast=yes verified=yes |
| 5 | fb565fa24c | terminated | 452.3k | 17.3k | 5.8k | 4m16s | 0 | 0 | 14 | 21 | 3 | 1 | yes | present | no | PASSED | code=no build=yes ast=yes verified=yes |
| 6 | 3bb3728754 | terminated | 28.1k | 232 | '- | 8s | 0 | 0 | 1 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 7 | 2252d478ac | terminated | 491.1k | 7.3k | 53.6k | 3m16s | 0 | 0 | 14 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 8 | 07cb178648 | terminated | 27.6k | 2.5k | '- | 48s | 0 | 0 | 1 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 9 | 9be7426f81 | terminated | 234.3k | 7.7k | 1.6k | 3m49s | 0 | 0 | 8 | 12 | 2 | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 10 | dc9647c0c4 | terminated | 283.0k | 6.4k | 8.7k | 4m07s | 0 | 0 | 10 | 22 | 7 | 1 | yes | present | no | FAILED | code=no build=no ast=yes verified=no |
| 11 | d23625828b | terminated | 442.3k | 6.8k | 113.1k | 2m57s | 0 | 0 | 11 | 12 | 7 | 1 | yes | present | no | PASSED | code=no build=yes ast=yes verified=yes |
| 12 | 63818ae8b6 | terminated | 26.3k | 308 | 4.8k | 17s | 0 | 0 | 1 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 13 | b0845a43b1 | terminated | 50.0k | 1.7k | 80 | 41s | 0 | 0 | 2 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 14 | b96e336c00 | terminated | 93.8k | 5.5k | '- | 1m26s | 0 | 0 | 3 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 15 | 6fd8123b8e | terminated | 86.0k | 4.9k | '- | 2m09s | 0 | 0 | 3 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 16 | d07321e810 | terminated | 517.0k | 16.5k | 6.5k | 6m52s | 0 | 0 | 16 | 28 | 3 | 1 | yes | present | no | PASSED | code=no build=yes ast=yes verified=yes |
| 17 | 2029f0be06 | terminated | 53.3k | 3.7k | 80 | 1m21s | 0 | 0 | 2 | 16 | '- | 1 | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 18 | f06b97c460 | terminated | 107.3k | 2.2k | 160 | 1m54s | 0 | 0 | 4 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 19 | f6ea1602d4 | terminated | 27.7k | 10.7k | '- | 1m07s | 0 | 0 | 1 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 20 | fd75fb13b1 | terminated | 27.0k | 1.8k | '- | 32s | 0 | 0 | 1 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 21 | e5aa1ba4ba | terminated | 976.8k | 13.7k | 13.8k | 6m37s | 0 | 0 | 22 | 31 | 9 | 3 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 22 | 6c61f6dd02 | terminated | 357.4k | 5.6k | 32.2k | 2m40s | 0 | 0 | 11 | 13 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 23 | 80e02adbda | terminated | 195.4k | 5.6k | 80 | 1m58s | 0 | 0 | 6 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 24 | 87fc783992 | terminated | 730.9k | 7.4k | 35.6k | 7m22s | 0 | 0 | 20 | 13 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 25 | 788bf7993e | terminated | 409.3k | 8.5k | 67.6k | 4m57s | 0 | 0 | 12 | 44 | 18 | 3 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 26 | 4f84c0c2cc | terminated | 66.1k | 4.4k | '- | 2m25s | 0 | 0 | 2 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 27 | e34784013b | terminated | 617.5k | 4.5k | 66.7k | 4m25s | 0 | 0 | 18 | 1 | 1 | 1 | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 28 | 1310a766b6 | terminated | 376.8k | 9.8k | 6.0k | 4m22s | 0 | 0 | 11 | 24 | 1 | 1 | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 29 | ff08c379ba | terminated | 413.6k | 6.6k | 66.2k | 2m42s | 0 | 0 | 12 | 21 | 2 | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 30 | e22bdc2c18 | terminated | 327.5k | 4.4k | 11.0k | 4m29s | 0 | 0 | 10 | 29 | 11 | 2 | yes | present | no | FAILED | code=no build=no ast=yes verified=no |
| 31 | a6e0ddc044 | terminated | 699.9k | 5.9k | 198.2k | 6m01s | 0 | 0 | 18 | 44 | 2 | 2 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 32 | 9b4dc5e216 | terminated | 689.1k | 7.5k | 37.9k | 6m18s | 0 | 0 | 20 | 42 | 2 | 2 | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 33 | 01487b6f72 | terminated | 450.4k | 8.4k | 1.0k | 5m05s | 0 | 0 | 13 | 67 | 37 | 1 | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 34 | 68b13743ff | terminated | 130.2k | 1.9k | 43 | 1m04s | 0 | 0 | 4 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 35 | 5d85f9abe8 | terminated | 179.8k | 2.0k | 13.8k | 2m07s | 0 | 0 | 5 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 36 | a89564a4b1 | terminated | 90.5k | 5.0k | '- | 2m56s | 0 | 0 | 5 | 4 | 1 | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 37 | c4f9ce85a7 | terminated | 117.5k | 2.5k | 21.6k | 1m16s | 0 | 0 | 5 | 36 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 38 | 0b85c884c7 | terminated | 132.0k | 5.0k | 160 | 1m39s | 0 | 0 | 6 | 32 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 39 | 83e7469df9 | terminated | 284.8k | 7.1k | 86 | 5m00s | 0 | 0 | 10 | 81 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 40 | 433691ace0 | terminated | 137.0k | 3.1k | 448 | 1m03s | 0 | 0 | 7 | 51 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 41 | ea675fe67d | terminated | 78.0k | 9.3k | 80 | 1m22s | 0 | 0 | 4 | 183 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 42 | 202c07a6a8 | terminated | 135.5k | 3.9k | 80 | 2m20s | 0 | 0 | 7 | 23 | 5 | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 43 | b659966744 | terminated | 447.6k | 3.9k | 31.3k | 3m04s | 0 | 0 | 13 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 44 | b152b1d569 | terminated | 892.3k | 24.0k | 72.1k | 8m42s | 0 | 0 | 28 | 22 | 12 | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 45 | 65308f41b5 | terminated | 54.0k | 3.2k | '- | 1m30s | 0 | 0 | 2 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 46 | e7fa479102 | terminated | 589.2k | 5.3k | 74.4k | 4m37s | 0 | 0 | 16 | 14 | 2 | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 47 | 536c51e4e0 | terminated | 265.2k | 7.0k | 6.4k | 5m19s | 0 | 0 | 11 | 49 | 3 | 1 | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 48 | ad6cfe8725 | terminated | 19.5k | 566 | 80 | 31s | 0 | 0 | 1 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 49 | 92d446f470 | terminated | 344.0k | 3.5k | 534 | 3m04s | 0 | 0 | 9 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 50 | a84d12c6f5 | terminated | 366.4k | 18.2k | 80 | 5m13s | 0 | 0 | 11 | 111 | 4 | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 51 | 1091fc3f83 | terminated | 34.9k | 3.1k | '- | 1m42s | 0 | 0 | 1 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 52 | a92d4efd6f | terminated | 491.5k | 5.7k | 5.4k | 4m11s | 0 | 0 | 12 | 1 | 1 | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 53 | 11370409e1 | terminated | 244.4k | 11.2k | 80 | 2m23s | 0 | 0 | 9 | 45 | 22 | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 54 | 19e50ebb3f | terminated | 54.8k | 744 | 528 | 36s | 0 | 0 | 3 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 55 | 035f3194e8 | terminated | 109.7k | 10.1k | 944 | 1m39s | 0 | 0 | 5 | 28 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 56 | be3f4b525a | terminated | 101.8k | 4.8k | 6.2k | 2m27s | 0 | 0 | 5 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 57 | 7eaeb97d00 | terminated | 133.8k | 3.1k | 24.9k | 2m58s | 0 | 0 | 7 | 60 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 58 | 78afa2e79e | terminated | 174.2k | 10.9k | 448 | 6m54s | 0 | 0 | 9 | '- | '- | '- | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 59 | 672d66f2b4 | terminated | 244.6k | 13.6k | 4.9k | 4m27s | 0 | 0 | 7 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 60 | d47dac14d4 | terminated | 582.8k | 9.5k | 672 | 5m49s | 0 | 0 | 18 | 19 | 12 | 2 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 61 | 00bc1ae521 | terminated | 88.0k | 3.4k | '- | 56s | 0 | 0 | 4 | 39 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 62 | 57e3d77216 | terminated | 385.4k | 9.2k | 1.0k | 6m30s | 0 | 0 | 18 | 21 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 63 | 2596a2048b | terminated | 36.7k | 3.1k | '- | 19s | 0 | 0 | 2 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 64 | 9337581331 | terminated | 107.3k | 63.9k | '- | 7m50s | 0 | 0 | 5 | 277 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 65 | c8f4146913 | terminated | 718.0k | 13.3k | 36.9k | 7m27s | 0 | 0 | 21 | 12 | 8 | 2 | yes | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 66 | 2c9c960826 | terminated | 77.2k | 1.4k | 6.5k | 43s | 0 | 0 | 4 | 48 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 67 | 2c630ec168 | terminated | 491.9k | 10.4k | '- | 6m02s | 0 | 0 | 14 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 68 | c2608a8330 | terminated | 383.3k | 9.4k | 651 | 3m36s | 0 | 0 | 12 | 10 | 1 | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 69 | 919236b7bb | terminated | 166.4k | 20.5k | 43 | 14m45s | 0 | 0 | 5 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 70 | 10b49b9051 | terminated | 173.3k | 4.0k | 35.1k | 1m23s | 0 | 0 | 5 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 71 | 91e0bd2cd6 | terminated | 757.8k | 6.7k | 44.3k | 5m55s | 0 | 0 | 21 | 1 | 8 | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 72 | ecb4f74186 | terminated | 235.8k | 5.2k | '- | 5m29s | 0 | 0 | 7 | 128 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 73 | cf0332cc16 | terminated | 166.9k | 4.1k | 336 | 1m44s | 0 | 0 | 5 | 116 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 74 | 8fdf699b10 | terminated | 163.0k | 3.8k | 26.0k | 58s | 0 | 0 | 9 | '- | '- | '- | yes | present | no | FAILED | code=yes build=yes ast=no verified=no |
| 75 | 93b404b1b8 | terminated | 98.8k | 7.5k | 448 | 1m41s | 0 | 0 | 5 | 15 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 76 | 0df170fbc9 | terminated | 108.0k | 2.3k | 7.9k | 2m15s | 0 | 0 | 6 | 7 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 77 | 723405b210 | terminated | 83.8k | 1.6k | '- | 37s | 0 | 0 | 5 | 18 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 78 | 0abcc36c48 | terminated | 50.3k | 909 | 7.5k | 30s | 0 | 0 | 3 | 11 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 79 | 32e42766c9 | terminated | 19.3k | 74 | '- | 9s | 0 | 0 | 1 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 80 | d9a72abda2 | terminated | 62.6k | 1.8k | 80 | 34s | 0 | 0 | 3 | 22 | '- | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 81 | c1ddd88e31 | terminated | 160.9k | 9.7k | '- | 3m15s | 0 | 0 | 7 | 22 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 82 | fcf7cd2d3f | terminated | 908.1k | 10.7k | 228.6k | 7m40s | 0 | 0 | 25 | 29 | 1 | 1 | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 83 | 8a09332e76 | terminated | 72.6k | 7.3k | 752 | 2m04s | 0 | 0 | 4 | 14 | 7 | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 84 | ff87149d7a | terminated | 19.8k | 516 | 80 | 19s | 0 | 0 | 1 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 85 | 8ac1436a69 | terminated | 57.0k | 2.0k | 448 | 1m14s | 0 | 0 | 3 | '- | '- | '- | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 86 | 3c290a01e9 | terminated | 103.1k | 6.7k | 816 | 2m51s | 0 | 0 | 5 | 21 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 87 | 6487ce427f | terminated | 607.8k | 17.6k | 53.0k | 8m35s | 0 | 0 | 14 | 210 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 88 | bf4e0bcb04 | terminated | 76.3k | 6.2k | '- | 59s | 0 | 0 | 2 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 89 | ace3b58f57 | terminated | 294.8k | 6.1k | 43.5k | 3m06s | 0 | 0 | 7 | 176 | 1 | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 90 | c864345cf2 | terminated | 25.0k | 1.5k | '- | 48s | 0 | 0 | 1 | '- | '- | '- | yes | present | no | FAILED | code=no build=no ast=no verified=no |
| 91 | cdde4f5ebf | terminated | 222.3k | 10.7k | 603 | 4m42s | 0 | 0 | 7 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 92 | 01e2412930 | terminated | 71.7k | 1.3k | 203 | 56s | 0 | 0 | 4 | 10 | 1 | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 93 | 10d3b63ab0 | terminated | 48.7k | 782 | 23.6k | 1m24s | 0 | 0 | 3 | 13 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 94 | a2cef089af | terminated | 51.7k | 1.7k | 6.4k | 58s | 0 | 0 | 3 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 95 | e4d0a8a862 | terminated | 195.0k | 7.0k | 6.2k | 1m33s | 0 | 0 | 6 | 69 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 96 | 8ca0406b72 | terminated | 254.9k | 10.2k | 560 | 2m08s | 0 | 0 | 9 | 12 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 97 | 351243a322 | terminated | 169.1k | 3.8k | 28.3k | 1m07s | 0 | 0 | 6 | '- | '- | '- | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 98 | af3bd321d7 | terminated | 132.1k | 6.0k | '- | 2m01s | 0 | 0 | 4 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 99 | 47567caf09 | terminated | 197.2k | 1.4k | 123 | 2m55s | 0 | 0 | 6 | 17 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 100 | 3dc4529d0d | terminated | 72.5k | 4.7k | '- | 36s | 0 | 0 | 4 | 7 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=no verified=no |
| 101 | 55c7ad9ed6 | terminated | 75.2k | 3.4k | 80 | 1m17s | 0 | 0 | 4 | 27 | '- | 1 | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 102 | 8ed79794aa | terminated | 75.2k | 3.4k | 80 | 1m17s | 0 | 0 | 4 | 27 | '- | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 103 | 9fdbe45938 | terminated | 550.7k | 7.3k | 1.3k | 3m45s | 0 | 0 | 19 | '- | '- | '- | yes | present | no | FAILED | code=yes build=no ast=yes verified=no |
| 104 | fbaedbfb05 | terminated | 319.5k | 6.2k | 65.7k | 3m28s | 0 | 0 | 10 | '- | '- | '- | yes | present | no | TIMEOUT | code=yes build=no ast=no verified=no |
| 105 | 2cc2103e78 | terminated | 158.2k | 2.3k | 30.4k | 1m36s | 0 | 0 | 5 | '- | '- | '- | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 106 | 4d3f12ccb5 | terminated | 88.7k | 1.2k | 34.7k | 46s | 0 | 0 | 3 | '- | '- | 1 | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 107 | 34f204dfb9 | terminated | 126.7k | 878 | 16.4k | 3m27s | 0 | 0 | 6 | '- | '- | '- | yes | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 108 | fc14fc9477 | terminated | 93.4k | 1.7k | 11.8k | 1m04s | 0 | 0 | 6 | 4 | '- | 1 | yes | present | no | TIMEOUT | code=yes build=no ast=no verified=no |
| 109 | 9055d08f6d | terminated | 93.4k | 1.7k | 11.8k | 1m04s | 0 | 0 | 6 | 4 | '- | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 110 | abba24f218 | terminated | 31.7k | 633 | 80 | 41s | 0 | 0 | 2 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 111 | 680e6e8477 | terminated | 41.8k | 767 | 5.4k | 1m42s | 0 | 0 | 2 | '- | '- | '- | yes | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 112 | 9acf9ec391 | terminated | 41.8k | 767 | 5.4k | 1m42s | 0 | 0 | 2 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 113 | e8762569e7 | terminated | 41.8k | 767 | 5.4k | 1m42s | 0 | 0 | 2 | '- | '- | '- | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 114 | 3002448897 | terminated | 21.3k | '- | '- | 5s | 0 | 0 | 0 | '- | '- | '- | yes | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 115 | 2a4b189773 | terminated | 18.8k | 510 | '- | 20s | 0 | 0 | 1 | 7 | '- | 1 | yes | present | no | TIMEOUT | code=yes build=yes ast=yes verified=yes |
| 116 | 922d14a467 | terminated | 32.0k | 650 | 80 | 1m25s | 0 | 0 | 2 | '- | '- | '- | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 117 | 632bbeb7b0 | terminated | 32.4k | 657 | 160 | 49s | 0 | 0 | 2 | '- | '- | '- | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 118 | 28f221ba08 | terminated | 58.5k | 1.6k | 19.6k | 1m13s | 0 | 0 | 3 | '- | '- | '- | yes | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 119 | b4ba03612d | terminated | 85.4k | 1.4k | 80 | 3m16s | 0 | 0 | 2 | '- | '- | '- | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 120 | 02c9b24005 | terminated | 42.0k | 429 | 80 | 22s | 0 | 0 | 1 | '- | '- | '- | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 121 | c7f3212f72 | terminated | 173.8k | 2.4k | 49.2k | 2m17s | 0 | 0 | 4 | '- | '- | '- | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 122 | 8354072cc9 | terminated | 171.4k | 915 | 160 | 1m16s | 0 | 0 | 4 | 5 | 1 | 1 | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 123 | afecc82086 | terminated | 83.9k | 1.3k | 6.3k | 58s | 0 | 0 | 2 | '- | '- | '- | no | present | no | TIMEOUT | code=no build=no ast=no verified=no |
| 124 | 4a77c830c0 | terminated | 61.9k | 779 | 36.9k | 1m00s | 0 | 0 | 4 | 11 | '- | 1 | yes | present | no | PASSED | code=yes build=yes ast=yes verified=yes |
| 125 | 6796e05bb7 | terminated | 61.9k | 779 | 36.9k | 1m00s | 0 | 0 | 4 | 11 | '- | 1 | no | present | no | FAILED | code=no build=no ast=no verified=no |
| 126 | f694d7be8c | terminated | 135.4k | 2.2k | 22.3k | 2m35s | 0 | 0 | 8 | 21 | '- | 1 | no | '- | no | '- |  |
| Summary |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Failed | 103 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Timed out | 16 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Success rate | 5% |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

**Total: 18 runs with complete per-task data.**

---
---

### qwen3.6-flash S1 SWE-Refactor (177 tasks)
Source: `swe_compound_qwen36flash_s1_FINAL.csv` | Rows: 177 | Columns: 13

| Nr | project | taskId | type | codeSuccessful | compileAndTestResult | refactoringMinerResult | successVerification | durationSeconds | agentDurationSeconds | copilotLspActionCount | timedOut | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | False | False | 222.3 | 55.7 | 4 | False | the code did not perform Extract And Move Method operation. |
| 2 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 142.0 | 102.9 | 4 | False | the Extract And Move Method operation is successful. |
| 3 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | False | False | 327.6 | 252.4 | 4 | False | the code did not perform Extract And Move Method operation. |
| 4 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | False | False | 109.8 | 109.8 | 4 | False | Extracted method must be public static. |
| 5 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | False | False | 81.8 | 81.8 | 4 | False | Extracted method must be public static. |
| 6 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 138.1 | 42.9 | 4 | False | the Extract And Move Method operation is successful. |
| 7 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 179.0 | 76.3 | 4 | False | the Extract And Move Method operation is successful. |
| 8 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 295.7 | 193.4 | 4 | False | the Extract And Move Method operation is successful. |
| 9 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 128.1 | 87.4 | 4 | False | the Extract And Move Method operation is successful. |
| 10 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 151.3 | 82.8 | 4 | False |  |
| 11 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 139.8 | 92.6 | 4 | False |  |
| 12 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 101.9 | 54.4 | 4 | False |  |
| 13 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | False | False | 267.8 | 123.7 | 4 | False | the code did not perform Extract And Move Method operation. |
| 14 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 214.6 | 163.8 | 4 | False |  |
| 15 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 156.8 | 88.0 | 4 | False | the Extract And Move Method operation is successful. |
| 16 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 249.8 | 198.2 | 4 | False |  |
| 17 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 163.5 | 131.7 | 4 | False | the Extract And Move Method operation is successful. |
| 18 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 170.9 | 115.5 | 4 | False |  |
| 19 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 157.2 | 109.1 | 4 | False |  |
| 20 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 168.4 | 95.9 | 4 | False | the Extract And Move Method operation is successful. |
| 21 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 134.6 | 64.0 | 4 | False | the Extract And Move Method operation is successful. |
| 22 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 158.2 | 83.6 | 4 | False | the Extract And Move Method operation is successful. |
| 23 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | False | False | 359.2 | 359.2 | 4 | False | Refactored code does not call extracted method 'validateFormatterType'. |
| 24 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 217.6 | 159.1 | 4 | False |  |
| 25 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 187.6 | 133.4 | 4 | False |  |
| 26 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 186.2 | 105.1 | 4 | False | the Extract And Move Method operation is successful. |
| 27 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 192.2 | 137.1 | 4 | False |  |
| 28 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | False | False | False | False | 390.4 | 390.4 | 4 | False | "Invalid target file path: ################# |
| 29 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 182.6 | 106.2 | 4 | False | the Extract And Move Method operation is successful. |
| 30 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 223.2 | 172.5 | 4 | False |  |
| 31 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 249.4 | 197.3 | 4 | False |  |
| 32 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | False | True | False | 200.7 | 165.8 | 4 | False | the Extract And Move Method operation is successful. |
| 33 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 124.6 | 73.7 | 4 | False |  |
| 34 | checkstyle | bfb3e5f5e416211bc95799426edba4 | Extract And Move Method | True | True | True | True | 326.6 | 272.0 | 4 | False |  |
| 35 | checkstyle | cd8ef61ea62f3155040501fd21e20b | Extract And Move Method | True | False | True | False | 598.0 | 220.3 | 4 | False | the Extract And Move Method operation is successful. |
| 36 | checkstyle | 7a9913aa64f911e41eae958b757e73 | Move And Rename Method | True | True | True | True | 373.9 | 86.8 | 4 | False |  |
| 37 | checkstyle | 664227cd5bf9c649847461d8055a7e | Extract And Move Method | False | False | False | False | 199.2 | 199.2 | 4 | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 38 | checkstyle | ba76f3e4f33194b0a1d687e95a5839 | Extract And Move Method | True | True | True | True | 279.8 | 68.4 | 4 | False |  |
| 39 | checkstyle | 1a6443b724a3539b000bcaa2ed9f80 | Extract And Move Method | True | False | True | False | 226.1 | 57.8 | 4 | False | the Extract And Move Method operation is successful. |
| 40 | checkstyle | 1a6443b724a3539b000bcaa2ed9f80 | Extract And Move Method | False | False | False | False | 138.2 | 138.2 | 4 | False | Invalid target file path: src/test/java/com/puppycrawl/tools/checkstyle/internal/utils/CheckUtil.jav |
| 41 | checkstyle | 1a6443b724a3539b000bcaa2ed9f80 | Extract And Move Method | True | False | True | False | 188.8 | 139.4 | 4 | False | the Extract And Move Method operation is successful. |
| 42 | checkstyle | 1a6443b724a3539b000bcaa2ed9f80 | Extract And Move Method | True | True | False | False | 136.6 | 100.4 | 4 | False | the code did not perform Extract And Move Method operation. |
| 43 | checkstyle | e2c6e148a92e01b3c6037b33440ee7 | Move And Inline Method | True | False | False | False | 138.8 | 110.7 | 4 | False | the code did not perform Move And Inline Method operation. |
| 44 | commons-io | 7566f557c2fa172d7677fcde06514e | Extract And Move Method | True | False | True | False | 350.6 | 114.9 | 4 | False | the Extract And Move Method operation is successful. |
| 45 | commons-io | a8ee7b9defba5ed7c83c1fa06b4020 | Extract And Move Method | True | False | True | False | 323.4 | 138.6 | 4 | False | the Extract And Move Method operation is successful. |
| 46 | commons-io | 7245fbd82735eed3fc5510f8b468b7 | Extract And Move Method | True | True | True | True | 604.5 | 70.1 | 4 | False |  |
| 47 | commons-io | c1692f43ef5a41328b54bbbcd06285 | Extract And Move Method | True | True | True | True | 267.8 | 87.8 | 4 | False |  |
| 48 | commons-io | b3ce147431dbad1bbd2e91d527560d | Extract And Move Method | True | False | True | False | 286.7 | 264.8 | 4 | False | the Extract And Move Method operation is successful. |
| 49 | commons-io | 8a786abb5e2cc04568517f1f8c0535 | Extract And Move Method | True | False | True | False | 131.8 | 104.1 | 4 | False | the Extract And Move Method operation is successful. |
| 50 | commons-io | 8a786abb5e2cc04568517f1f8c0535 | Extract And Move Method | True | False | False | False | 73.6 | 55.9 | 4 | False | the code did not perform Extract And Move Method operation. |
| 51 | commons-io | 8a786abb5e2cc04568517f1f8c0535 | Extract And Move Method | True | False | False | False | 144.5 | 125.0 | 4 | False | the code did not perform Extract And Move Method operation. |
| 52 | commons-io | 0d84f279d6dd6486b581acf2ea2ad2 | Extract And Move Method | True | False | True | False | 110.0 | 89.8 | 4 | False | the Extract And Move Method operation is successful. |
| 53 | commons-lang | 479532b83db2d7b228e4128f2db022 | Extract And Move Method | True | False | False | False | 193.5 | 152.8 | 4 | False | the code did not perform Extract And Move Method operation. |
| 54 | commons-lang | cdddb82e12ef7b2cc770125e930bde | Extract And Move Method | True | True | True | True | 518.7 | 73.3 | 4 | False |  |
| 55 | commons-lang | cdddb82e12ef7b2cc770125e930bde | Extract And Move Method | True | True | True | True | 518.7 | 73.3 | 4 | False |  |
| 56 | commons-lang | e4c03c5e38b3e2550da7a1f9084d93 | Extract And Move Method | False | False | False | False | 17.2 | 17.2 | 4 | True | Invalid target file path: |
| 57 | guava | a9c3d3ac68223c83a98022eb88bbcf | Move And Rename Method | True | False | True | False | 656.0 | 174.9 | 4 | False | the Move And Rename Method operation is successful. |
| 58 | guava | a9c3d3ac68223c83a98022eb88bbcf | Move And Rename Method | True | False | False | False | 376.8 | 280.4 | 4 | False | the code did not perform Move And Rename Method operation. |
| 59 | guava | a9c3d3ac68223c83a98022eb88bbcf | Move And Rename Method | True | False | False | False | 595.7 | 178.9 | 4 | False | the code did not perform Move And Rename Method operation. |
| 60 | guava | b03067f2c78b2352cba8f5136c9aa0 | Move And Rename Method | False | False | False | False | 154.6 | 154.6 | 4 | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 61 | guava | b03067f2c78b2352cba8f5136c9aa0 | Move And Rename Method | True | False | False | False | 115.8 | 115.8 | 4 | False | Moved method must be public static. |
| 62 | guava | b007d6db4ab71c5fc94623cac6eb8a | Extract And Move Method | True | False | True | False | 502.8 | 303.1 | 4 | False | the Extract And Move Method operation is successful. |
| 63 | guava | ee9ac70a9296645b3f883773eb9509 | Extract And Move Method | True | False | True | False | 829.9 | 710.2 | 4 | False | the Extract And Move Method operation is successful. |
| 64 | guava | ee9ac70a9296645b3f883773eb9509 | Extract And Move Method | True | False | True | False | 285.7 | 187.5 | 4 | False | the Extract And Move Method operation is successful. |
| 65 | hibernate-orm | 96cba56591e3e8c6dabaf35d954bd5 | Extract And Move Method | True | False | True | False | 1312.8 | 209.8 | 4 | False | the Extract And Move Method operation is successful. |
| 66 | hibernate-orm | 2f7052c0ce5114e492c7dc4e4b8abd | Extract And Move Method | True | False | False | False | 1216.1 | 137.6 | 4 | False | the code did not perform Extract And Move Method operation. |
| 67 | hibernate-orm | 5dcbdf64f11dfdcf25fd5a4a571f97 | Extract And Move Method | True | False | False | False | 355.8 | 355.8 | 4 | False | Extracted method must be public static. |
| 68 | hibernate-orm | 72e2da2da84fae761f14ceeb822bd3 | Move And Inline Method | False | False | False | False | 24.5 | 24.5 | 4 | False | "Invalid target file path: ########################## |
| 69 | hibernate-orm | ba05533a036e73ac119169392b0da4 | Extract And Move Method | True | False | False | False | 144.8 | 144.8 | 4 | False | Extracted method must be public static. |
| 70 | hibernate-orm | 26e73937756de5781043f120905b71 | Extract And Move Method | True | True | True | True | 368.8 | 115.2 | 4 | False |  |
| 71 | hibernate-orm | 26e73937756de5781043f120905b71 | Extract And Move Method | True | True | True | True | 368.8 | 115.2 | 4 | False |  |
| 72 | hibernate-orm | 26e73937756de5781043f120905b71 | Extract And Move Method | True | True | True | True | 368.8 | 115.2 | 4 | False |  |
| 73 | hibernate-orm | 26e73937756de5781043f120905b71 | Extract And Move Method | True | True | True | True | 368.8 | 115.2 | 4 | False |  |
| 74 | hibernate-orm | c04caa18de3c5ff81c17ebb151430b | Extract And Move Method | True | True | True | True | 346.2 | 85.8 | 4 | False |  |
| 75 | hibernate-search | b67c74bdf7a5a1a8102fb0b0179bdc | Move And Inline Method | True | False | False | False | 1360.2 | 129.7 | 4 | False | the code did not perform Move And Inline Method operation. |
| 76 | hibernate-search | b67c74bdf7a5a1a8102fb0b0179bdc | Move And Inline Method | True | False | False | False | 451.4 | 131.3 | 4 | False | the code did not perform Move And Inline Method operation. |
| 77 | hibernate-search | b67c74bdf7a5a1a8102fb0b0179bdc | Move And Inline Method | True | False | False | False | 462.3 | 87.5 | 4 | False | the code did not perform Move And Inline Method operation. |
| 78 | hibernate-search | b67c74bdf7a5a1a8102fb0b0179bdc | Move And Inline Method | True | False | False | False | 454.3 | 153.2 | 4 | False | the code did not perform Move And Inline Method operation. |
| 79 | hibernate-search | ea4e402fd1d991e8c01ae391804779 | Move And Rename Method | True | False | True | False | 1298.0 | 56.6 | 4 | False | the Move And Rename Method operation is successful. |
| 80 | hibernate-search | f50cbfc772b75e7d7a983359b9baca | Move And Rename Method | True | False | False | False | 127.3 | 127.0 | 4 | False | Target file path does not exist: /util/internal/test/src/main/java/org/hibernate/search/util/impl/te |
| 81 | hibernate-search | 0b4c69d582f4c29554d78da38daebb | Extract And Move Method | True | True | True | True | 2106.8 | 104.8 | 4 | False |  |
| 82 | hibernate-search | c1738e3fcb5ac2ded491a9ff1b9aa6 | Move And Rename Method | True | False | False | False | 109.9 | 109.9 | 4 | False | Refactored code does not call moved method 'fromClusterMemberList'. |
| 83 | hibernate-search | 520908200e1e83c994b39a93131741 | Extract And Move Method | True | False | True | False | 610.3 | 230.4 | 4 | False | the Extract And Move Method operation is successful. |
| 84 | hibernate-search | b369ab192fd1c80ab666c63e65224b | Extract And Move Method | True | False | True | False | 228.6 | 67.9 | 4 | False | the Extract And Move Method operation is successful. |
| 85 | hibernate-search | 314cff098d6147b783fa091ce3ebcc | Move And Rename Method | True | True | False | False | 2077.2 | 54.0 | 4 | False | the code did not perform Move And Rename Method operation. |
| 86 | hibernate-search | 314cff098d6147b783fa091ce3ebcc | Move And Rename Method | True | False | False | False | 57.7 | 57.7 | 4 | False | Refactored code does not call moved method 'getPersistenceUnitName'. |
| 87 | hibernate-search | 6b65d5b3d028b6cf672822b29edb96 | Move And Inline Method | True | False | False | False | 361.0 | 154.5 | 4 | False | the code did not perform Move And Inline Method operation. |
| 88 | hibernate-search | da64c4e549b8dfd9c17e7753247d80 | Extract And Move Method | True | True | True | True | 3360.7 | 104.5 | 4 | False |  |
| 89 | hibernate-search | 05c12b8fd2eb002ad9246efd04d8fa | Extract And Move Method | True | False | True | False | 287.1 | 111.5 | 4 | False | the Extract And Move Method operation is successful. |
| 90 | hibernate-search | 0c6c0d87a14968fd7a417b4943835c | Move And Inline Method | True | False | False | False | 118.5 | 63.7 | 4 | False | the code did not perform Move And Inline Method operation. |
| 91 | hibernate-search | 14e6370a9ab5e7fca20e508f6413bd | Move And Rename Method | True | False | False | False | 84.1 | 83.9 | 4 | False | Target file path does not exist: /engine/src/main/java/org/hibernate/search/engine/environment/class |
| 92 | hibernate-search | 60720a3723b836213b0e663b71fcbd | Move And Rename Method | True | False | False | False | 58.3 | 58.3 | 4 | False | Moved method must be public static. |
| 93 | hibernate-search | daaa9ff20cae0f7751636f16bcaf0c | Extract And Move Method | True | False | False | False | 71.7 | 71.7 | 4 | False | Extracted method must be public static. |
| 94 | hibernate-search | f6398f46e661b12bb5cd7d429c52bd | Extract And Move Method | True | True | False | False | 1264.8 | 176.0 | 4 | False | the code did not perform Extract And Move Method operation. |
| 95 | hibernate-search | 8233e6e5e455472b841a7a2b0aee22 | Extract And Move Method | True | True | True | True | 815.7 | 73.6 | 4 | False |  |
| 96 | hibernate-search | be929dfca72583e5cef800af2f9772 | Extract And Move Method | True | False | False | False | 269.2 | 220.6 | 4 | False | the code did not perform Extract And Move Method operation. |
| 97 | hibernate-search | daaa9ff20cae0f7751636f16bcaf0c | Extract And Move Method | True | True | True | True | 345.6 | 51.4 | 4 | False |  |
| 98 | hibernate-search | daaa9ff20cae0f7751636f16bcaf0c | Extract And Move Method | True | True | True | True | 375.0 | 200.9 | 4 | False |  |
| 99 | hibernate-search | 4c0595551f48dcca939fc3f7d3ea5b | Move And Rename Method | True | False | True | False | 326.5 | 100.5 | 4 | False | the Move And Rename Method operation is successful. |
| 100 | hibernate-search | 6b55b85d003d11848939dbdf2640fc | Move And Rename Method | True | False | False | False | 139.0 | 139.0 | 4 | False | Refactored code does not call moved method 'getTargetDir'. |
| 101 | hibernate-search | 64d26592b1ac48943690f7690355d4 | Move And Inline Method | False | False | False | False | 128.8 | 128.7 | 4 | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 102 | hibernate-search | 4809368dec30478582c165d2c01aa2 | Extract And Move Method | True | False | True | False | 702.9 | 219.0 | 4 | False | the Extract And Move Method operation is successful. |
| 103 | hibernate-search | f307576b2d1a89c3814067a2b6b62d | Extract And Move Method | True | False | False | False | 854.7 | 191.7 | 4 | False | the code did not perform Extract And Move Method operation. |
| 104 | hibernate-search | 3ba4b03373611f27e258496ad8376e | Extract And Move Method | True | False | False | False | 158.9 | 158.4 | 4 | False | Target file path does not exist: /workspace/benchmarks/swe-refactor/data/hibernate-search/ai_logs/si |
| 105 | hibernate-search | 3ba4b03373611f27e258496ad8376e | Extract And Move Method | True | False | False | False | 136.7 | 92.5 | 4 | False | the code did not perform Extract And Move Method operation. |
| 106 | javaparser | b08e66263903837d53a688b5d12a75 | Extract And Move Method | False | False | False | False | 71.6 | 71.5 | 4 | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 107 | javaparser | 2903fc918dd87be53192aa10650473 | Move And Inline Method | True | True | False | False | 367.9 | 113.9 | 4 | False | the code did not perform Move And Inline Method operation. |
| 108 | javaparser | 034b17a06497b52eb066eaf1ece5f0 | Extract And Move Method | False | False | True | False | 214.6 | 65.6 | 4 | False | the Extract And Move Method operation is successful. |
| 109 | javaparser | ead1412d06bf2ba7eaec982231023a | Move And Inline Method | False | False | False | False | 149.5 | 149.5 | 4 | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 110 | javaparser | 547da782d2ea7f1abc35e5c1e58529 | Extract And Move Method | True | True | True | True | 57.7 | 39.4 | 4 | False |  |
| 111 | javaparser | c378a677ebcd999d853b3e5867ac7c | Extract And Move Method | True | False | True | False | 393.5 | 106.9 | 4 | False | the Extract And Move Method operation is successful. |
| 112 | javaparser | 2b503c32229deae7d432f59dab7108 | Extract And Move Method | True | False | True | False | 396.1 | 45.4 | 4 | False | the Extract And Move Method operation is successful. |
| 113 | javaparser | 78d0ea5d493f0ab2e83bb70d7023b6 | Extract And Move Method | True | False | False | False | 68.0 | 51.0 | 4 | False | the code did not perform Extract And Move Method operation. |
| 114 | javaparser | 86f41353d40bfd3ef0669b86392662 | Extract And Move Method | False | False | False | False | 270.2 | 270.2 | 4 | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 115 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 1472.7 | 188.3 | 4 | False | the Extract And Move Method operation is successful. |
| 116 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 1167.9 | 190.9 | 4 | False | the Extract And Move Method operation is successful. |
| 117 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | True | True | True | 1004.2 | 134.6 | 4 | False |  |
| 118 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 2013.4 | 817.5 | 4 | False | the Extract And Move Method operation is successful. |
| 119 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | False | False | 101.7 | 101.7 | 4 | False | Extracted method must be public static. |
| 120 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | False | False | False | False | 216.7 | 216.7 | 4 | True | Extracted method must be public static. |
| 121 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 1124.0 | 157.4 | 4 | True | the Extract And Move Method operation is successful. |
| 122 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 1072.8 | 100.6 | 4 | False | the Extract And Move Method operation is successful. |
| 123 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 1037.7 | 80.9 | 4 | False | the Extract And Move Method operation is successful. |
| 124 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | False | False | False | False | 144.8 | 144.8 | 4 | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 125 | junit5 | 2a777a84cfdc9ccb79aa906cde80e0 | Move And Rename Method | True | False | False | False | 738.6 | 123.2 | 4 | False | the code did not perform Move And Rename Method operation. |
| 126 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | False | False | 1130.3 | 104.9 | 4 | False | the code did not perform Extract And Move Method operation. |
| 127 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 1143.2 | 96.4 | 4 | False | the Extract And Move Method operation is successful. |
| 128 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 1175.0 | 146.9 | 4 | False | the Extract And Move Method operation is successful. |
| 129 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | False | False | 1197.9 | 230.3 | 4 | False | the code did not perform Extract And Move Method operation. |
| 130 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | False | False | False | False | 134.2 | 134.2 | 4 | False | invalid_swe_output_artifact: missing required original SWE section headers or malformed final SWE ou |
| 131 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | False | False | 1159.6 | 197.8 | 4 | False | the code did not perform Extract And Move Method operation. |
| 132 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | True | False | 1231.9 | 223.0 | 4 | False | the Extract And Move Method operation is successful. |
| 133 | junit5 | 50b28568a20c85473460504f484ac8 | Extract And Move Method | True | False | False | False | 1132.9 | 139.7 | 4 | False | the code did not perform Extract And Move Method operation. |
| 134 | junit5 | 9f6ad01b6d4753a0cb8f6c366371b2 | Move And Rename Method | True | False | False | False | 238.0 | 75.3 | 4 | False | the code did not perform Move And Rename Method operation. |
| 135 | mockito | 50b21cf68b400a29369de58b9286d2 | Extract And Move Method | True | True | True | True | 406.9 | 35.0 | 4 | False |  |
| 136 | pmd | 994b8402d59773888977d768d39552 | Extract And Move Method | True | False | True | False | 2000.9 | 73.8 | 4 | False | the Extract And Move Method operation is successful. |
| 137 | pmd | e4f5d027b2d86f675208d8da53d0bb | Extract And Move Method | True | False | False | False | 494.8 | 84.2 | 4 | False | the code did not perform Extract And Move Method operation. |
| 138 | pmd | 868883819020b0780313358e00f613 | Move And Rename Method | True | False | True | False | 109.6 | 74.5 | 4 | False | the Move And Rename Method operation is successful. |
| 139 | pmd | 20a3c39b4d88b0e5716b9e72880ad9 | Extract And Move Method | True | True | True | True | 1863.1 | 83.8 | 4 | False |  |
| 140 | pmd | 91d0ebf4620b9cda44ce6f02232fe8 | Extract And Move Method | True | False | False | False | 122.4 | 122.4 | 4 | False | Extracted method must be public static. |
| 141 | pmd | 97c08a37ab6e5f0dc0bc2c38d86520 | Extract And Move Method | True | False | True | False | 1107.4 | 178.2 | 4 | False | the Extract And Move Method operation is successful. |
| 142 | pmd | da03fafabb2146ca3b2cd3f6148475 | Extract And Move Method | False | False | False | False | 51.0 | 51.0 | 4 | True | Invalid target file path: |
| 143 | pmd | a733da4dcfa19b80f21480040aaf70 | Move And Inline Method | True | False | False | False | 99.7 | 63.2 | 4 | False | the code did not perform Move And Inline Method operation. |
| 144 | pmd | 0276320abf2c66cae14d2ad24e2b2f | Move And Inline Method | False | False | False | False | 16.4 | 16.4 | 4 | True | "Invalid target file path: ########################## |
| 145 | pmd | 05870c98cc05805d6272d12f5080af | Extract And Move Method | True | True | True | True | 588.9 | 116.5 | 4 | False |  |
| 146 | pmd | 05870c98cc05805d6272d12f5080af | Extract And Move Method | True | False | True | False | 161.7 | 133.5 | 4 | False | the Extract And Move Method operation is successful. |
| 147 | pmd | 5031c83c880d11f215b2b21919ff30 | Extract And Move Method | False | False | False | False | 15.9 | 15.9 | 4 | True | Invalid target file path: |
| 148 | pmd | 00d391261d90afb005aac22dd9e1be | Extract And Move Method | True | False | True | False | 2137.7 | 241.7 | 4 | False | the Extract And Move Method operation is successful. |
| 149 | pmd | 5dc2774c0a53810717358cc850b69c | Extract And Move Method | True | False | True | False | 262.0 | 233.2 | 4 | False | the Extract And Move Method operation is successful. |
| 150 | pmd | cfbb14c91c24b1a50cf4b41cd855fd | Extract And Move Method | True | False | True | False | 111.4 | 74.5 | 4 | False | the Extract And Move Method operation is successful. |
| 151 | pmd | cfbb14c91c24b1a50cf4b41cd855fd | Extract And Move Method | True | False | True | False | 100.4 | 66.7 | 4 | False | the Extract And Move Method operation is successful. |
| 152 | pmd | cfbb14c91c24b1a50cf4b41cd855fd | Extract And Move Method | True | False | True | False | 141.3 | 106.7 | 4 | False | the Extract And Move Method operation is successful. |
| 153 | pmd | 214e80a5f1d68e3b42efeacab5b0fc | Extract And Move Method | True | False | True | False | 154.4 | 121.6 | 4 | False | the Extract And Move Method operation is successful. |
| 154 | pmd | ff2f5ef93c1b3150583e9611b2a8fd | Move And Rename Method | True | False | True | False | 139.3 | 99.1 | 4 | False | the Move And Rename Method operation is successful. |
| 155 | pmd | 2123ab3d5d7dcfc867ada3af119c3d | Extract And Move Method | True | True | True | True | 1104.1 | 57.4 | 4 | False |  |
| 156 | pmd | a70e70ad15995e87060380ee241e36 | Extract And Move Method | True | True | False | False | 588.7 | 64.7 | 4 | False | the code did not perform Extract And Move Method operation. |
| 157 | pmd | 26bcbd839a79055a0ff037da3c8c54 | Move And Inline Method | True | True | False | False | 527.3 | 190.9 | 4 | False | the code did not perform Move And Inline Method operation. |
| 158 | pmd | 05870c98cc05805d6272d12f5080af | Extract And Move Method | True | False | True | False | 123.0 | 88.8 | 4 | False | the Extract And Move Method operation is successful. |
| 159 | pmd | 05870c98cc05805d6272d12f5080af | Extract And Move Method | True | False | True | False | 397.2 | 96.6 | 4 | False | the Extract And Move Method operation is successful. |
| 160 | pmd | 05870c98cc05805d6272d12f5080af | Extract And Move Method | True | False | True | False | 1284.6 | 182.3 | 4 | False | the Extract And Move Method operation is successful. |
| 161 | pmd | 05870c98cc05805d6272d12f5080af | Extract And Move Method | True | True | True | True | 610.6 | 70.8 | 4 | False |  |
| 162 | pmd | 5c36ee1eba5a08732d6fc53b0a6901 | Extract And Move Method | True | False | True | False | 182.0 | 125.1 | 4 | False | the Extract And Move Method operation is successful. |
| 163 | pmd | bc25e58dfc8b3fe32c173e2cf213bf | Extract And Move Method | True | True | True | True | 741.1 | 54.1 | 4 | False |  |
| 164 | pmd | ff2f5ef93c1b3150583e9611b2a8fd | Move And Rename Method | True | False | False | False | 251.4 | 213.6 | 4 | False | the code did not perform Move And Rename Method operation. |
| 165 | pmd | 396567636fa1dbef2f7766f8c9ef57 | Extract And Move Method | True | True | True | True | 648.3 | 86.3 | 4 | False |  |
| 166 | pmd | 6253b696ea9b04ecf4a0c832473a17 | Extract And Move Method | True | False | True | False | 1035.5 | 130.7 | 4 | False | the Extract And Move Method operation is successful. |
| 167 | pmd | 08b19dbcdde5d6258515cf2620a855 | Extract And Move Method | True | True | True | True | 891.8 | 62.2 | 4 | False |  |
| 168 | pmd | 1540ec6d9148fc14fc1673f4df1d33 | Move And Rename Method | True | False | False | False | 322.4 | 322.4 | 4 | False | Refactored code does not call moved method 'data'. |
| 169 | pmd | 2995f156caf2b55369ef28108f0b60 | Extract And Move Method | True | False | False | False | 461.4 | 139.6 | 4 | False | the code did not perform Extract And Move Method operation. |
| 170 | pmd | 0fec3640a30bd92e6a2d2a0f318883 | Extract And Move Method | True | True | True | True | 1422.2 | 44.3 | 4 | False |  |
| 171 | pmd | 5f2a5bb67813ac5acb38a8bac6d335 | Extract And Move Method | True | True | True | True | 495.0 | 42.0 | 4 | False |  |
| 172 | shenyu | d8c7b57eed6c5ab5880cca8f49920e | Extract And Move Method | False | False | False | False | 73.1 | 73.1 | 4 | False | Invalid target file path: |
| 173 | shenyu | 18b3ac1bfe19cbe26650e13d9cb1ad | Extract And Move Method | True | True | False | False | 8192.8 | 67.6 | 4 | False | the code did not perform Extract And Move Method operation. |
| 174 | shenyu | 9725874eaa20ec87a3d8beea168f3a | Extract And Move Method | True | True | True | True | 3478.3 | 52.3 | 4 | False |  |
| 175 | shenyu | 2f4ff7f4b7100db14c549f47941fff | Extract And Move Method | True | False | True | False | 451.5 | 75.2 | 4 | False | the Extract And Move Method operation is successful. |
| 176 | zxing | 515688992bec0973288f3deb9b4538 | Extract And Move Method | True | False | True | False | 259.6 | 221.7 | 4 | False | the Extract And Move Method operation is successful. |
| 177 | zxing | 515688992bec0973288f3deb9b4538 | Extract And Move Method | True | False | False | False | 527.3 | 496.5 | 4 | False | the code did not perform Extract And Move Method operation. |
---



---

### qwen3.6-flash S1 base RefactorBench
Source: `refbench_base_qwen36flash_s1.csv` | Rows: 107 | Columns: 2
  Run ID,benchmark_pipeline_20260517_122537 | Status,completed

| Model | qwen/qwen3.6-flash |
|---|---|
| Datasets | refbench |
| Setups | s1_default |
| # | Task |
| 1 | add-log-parameter-get-group-vars |
| 2 | add-log-parameter-is-systemd-managed |
| 3 | combine-namespace-compat |
| 4 | data-to-inventory-data |
| 5 | move-quoting-splitter |
| 6 | new-inventory-patterns |
| 7 | new-utils-class-connection |
| 8 | new-utils-from-basic |
| 9 | parse_key_value |
| 10 | rename-lenient-lowercase |
| 11 | sort-groups-to-group-sort |
| 12 | add-log-parameter-get-digest-algorithm |
| 13 | add-log-parameter-node-format |
| 14 | annotation-utils |
| 15 | autoretry-to-retry |
| 16 | combine-unpickle-task |
| 17 | dump-message-to-serialization |
| 18 | ensure_serialize |
| 19 | evaluate-promises-to-serialization |
| 20 | expand-router-string-to-utils |
| 21 | object-mro-lookup |
| 22 | rename-host-format |
| 23 | truncate-text |
| 24 | add-log-parameter-constant-time-compare |
| 25 | add-log-parameter-get-resolver |
| 26 | add-log-parameter-resolve-error-handler |
| 27 | add-none-handling-duration-string |
| 28 | combine-utils-dates-dateformat |
| 29 | combine-utils-hashable-itercompat |
| 30 | new-converter-to-python-class |
| 31 | new-path-traversal-exception |
| 32 | new-reference-context-field-class |
| 33 | new-reference-context-graph-class |
| 34 | new-timezone-class |
| 35 | new-utils-adapt-method-mode |
| 36 | new-utils-check-response |
| 37 | new-utils-path-from-module |
| 38 | remove-core-cache-utils |
| 39 | remove-db-models-constants |
| 40 | rename-file-move-safe |
| 41 | split-parse-apps-and-model-labels |
| 42 | add-log-parameter-generate-option-id-for-path |
| 43 | exception-handlers-to-handlers |
| 44 | get-auth-scheme-param |
| 45 | openapi-get-utils |
| 46 | params-to-param |
| 47 | value-is-a-sequence |
| 48 | add-log-parameter-get-debug-flag |
| 49 | add-log-parameter-get-flashed-messages |
| 50 | debughelpers-to-helpers.py |
| 51 | rename-send-from-directory |
| 52 | render-template-str |
| 53 | stream-template-str |
| 54 | add-log-parameter-get-encoding-from-headers |
| 55 | add-log-parameter-resolve-proxies |
| 56 | add-log-parameter-select-proxy |
| 57 | combine-from-key-to-key |
| 58 | combine-internal-utils-utils |
| 59 | move-hooks-sessions |
| 60 | new-cookie-utils-class |
| 61 | rename-lookup-dict-dict-lookup |
| 62 | rename-super-len-complex-len |
| 63 | split-warnings-exceptions |
| 64 | add-log-parameter-delete-directory |
| 65 | add-log-parameter-get-capability-definitions |
| 66 | add-log-parameter-recursive-diff |
| 67 | cant-create |
| 68 | channel-to-transport |
| 69 | ex-pillar-fail |
| 70 | ex-state-fail |
| 71 | exactly-n-boto-mod |
| 72 | get-unavail |
| 73 | iam-to-aws |
| 74 | mksls-to-specific |
| 75 | namecheap-xmlutil |
| 76 | paged-call-boto-mod |
| 77 | pem-fingerprint |
| 78 | perm-denied |
| 79 | add-log-parameter-disconnect-all |
| 80 | add-log-parameter-job-dir |
| 81 | add-log-parameter-xmliter |
| 82 | genspider-functions-to-utils-url |
| 83 | new-downloadermiddlewares-utils |
| 84 | new-spider-utils-in-spiders |
| 85 | new-verify-reactor-class |
| 86 | not-supported-exception-to-unsupported |
| 87 | parameterize-gunzip |
| 88 | rename-description-commands |
| 89 | rename-engine-status |
| 90 | rename-processtest-testproc |
| 91 | sitemap-url-to-url |
| 92 | global-objects |
| 93 | log-utils |
| 94 | option-parser-with-pretty-print |
| 95 | options-utils |
| 96 | remove-locale-data |
| 97 | rename-http1connection |
| 98 | rename-to-camel-case |
| 99 | resolvers-as-separate |
| 100 | tcpclient-connect-params |
| Summary |  |
| Failed | 26 |
| Timed out | 15 |
| Success rate | 59% |

---

### qwen3.6-flash S1 lazy RefactorBench
Source: `refbench_lazy_qwen36flash_s1.csv` | Rows: 107 | Columns: 2
  Run ID,benchmark_pipeline_20260517_122814 | Status,completed

| Model | qwen/qwen3.6-flash |
|---|---|
| Datasets | refbench |
| Setups | s1_default |
| # | Task |
| 1 | add-log-parameter-get-group-vars |
| 2 | add-log-parameter-is-systemd-managed |
| 3 | combine-namespace-compat |
| 4 | data-to-inventory-data |
| 5 | move-quoting-splitter |
| 6 | new-inventory-patterns |
| 7 | new-utils-class-connection |
| 8 | new-utils-from-basic |
| 9 | parse_key_value |
| 10 | rename-lenient-lowercase |
| 11 | sort-groups-to-group-sort |
| 12 | add-log-parameter-get-digest-algorithm |
| 13 | add-log-parameter-node-format |
| 14 | annotation-utils |
| 15 | autoretry-to-retry |
| 16 | combine-unpickle-task |
| 17 | dump-message-to-serialization |
| 18 | ensure_serialize |
| 19 | evaluate-promises-to-serialization |
| 20 | expand-router-string-to-utils |
| 21 | object-mro-lookup |
| 22 | rename-host-format |
| 23 | truncate-text |
| 24 | add-log-parameter-constant-time-compare |
| 25 | add-log-parameter-get-resolver |
| 26 | add-log-parameter-resolve-error-handler |
| 27 | add-none-handling-duration-string |
| 28 | combine-utils-dates-dateformat |
| 29 | combine-utils-hashable-itercompat |
| 30 | new-converter-to-python-class |
| 31 | new-path-traversal-exception |
| 32 | new-reference-context-field-class |
| 33 | new-reference-context-graph-class |
| 34 | new-timezone-class |
| 35 | new-utils-adapt-method-mode |
| 36 | new-utils-check-response |
| 37 | new-utils-path-from-module |
| 38 | remove-core-cache-utils |
| 39 | remove-db-models-constants |
| 40 | rename-file-move-safe |
| 41 | split-parse-apps-and-model-labels |
| 42 | add-log-parameter-generate-option-id-for-path |
| 43 | exception-handlers-to-handlers |
| 44 | get-auth-scheme-param |
| 45 | openapi-get-utils |
| 46 | params-to-param |
| 47 | value-is-a-sequence |
| 48 | add-log-parameter-get-debug-flag |
| 49 | add-log-parameter-get-flashed-messages |
| 50 | debughelpers-to-helpers.py |
| 51 | rename-send-from-directory |
| 52 | render-template-str |
| 53 | stream-template-str |
| 54 | add-log-parameter-get-encoding-from-headers |
| 55 | add-log-parameter-resolve-proxies |
| 56 | add-log-parameter-select-proxy |
| 57 | combine-from-key-to-key |
| 58 | combine-internal-utils-utils |
| 59 | move-hooks-sessions |
| 60 | new-cookie-utils-class |
| 61 | rename-lookup-dict-dict-lookup |
| 62 | rename-super-len-complex-len |
| 63 | split-warnings-exceptions |
| 64 | add-log-parameter-delete-directory |
| 65 | add-log-parameter-get-capability-definitions |
| 66 | add-log-parameter-recursive-diff |
| 67 | cant-create |
| 68 | channel-to-transport |
| 69 | ex-pillar-fail |
| 70 | ex-state-fail |
| 71 | exactly-n-boto-mod |
| 72 | get-unavail |
| 73 | iam-to-aws |
| 74 | mksls-to-specific |
| 75 | namecheap-xmlutil |
| 76 | paged-call-boto-mod |
| 77 | pem-fingerprint |
| 78 | perm-denied |
| 79 | add-log-parameter-disconnect-all |
| 80 | add-log-parameter-job-dir |
| 81 | add-log-parameter-xmliter |
| 82 | genspider-functions-to-utils-url |
| 83 | new-downloadermiddlewares-utils |
| 84 | new-spider-utils-in-spiders |
| 85 | new-verify-reactor-class |
| 86 | not-supported-exception-to-unsupported |
| 87 | parameterize-gunzip |
| 88 | rename-description-commands |
| 89 | rename-engine-status |
| 90 | rename-processtest-testproc |
| 91 | sitemap-url-to-url |
| 92 | global-objects |
| 93 | log-utils |
| 94 | option-parser-with-pretty-print |
| 95 | options-utils |
| 96 | remove-locale-data |
| 97 | rename-http1connection |
| 98 | rename-to-camel-case |
| 99 | resolvers-as-separate |
| 100 | tcpclient-connect-params |
| Summary |  |
| Failed | 42 |
| Timed out | 14 |
| Success rate | 44% |

---

### qwen3.6-flash S1 desc+LSP RefactorBench
Source: `refbench_descriptive-lsp-qwen3.6-flash_s1.csv` | Rows: 107 | Columns: 2
  Run ID,benchmark_pipeline_20260509_045651 | Status,completed

| Model | qwen/qwen3.6-flash |
|---|---|
| Datasets | refbench |
| Setups | s1_default |
| # | Task |
| 1 | add-log-parameter-get-group-vars |
| 2 | add-log-parameter-is-systemd-managed |
| 3 | combine-namespace-compat |
| 4 | data-to-inventory-data |
| 5 | move-quoting-splitter |
| 6 | new-inventory-patterns |
| 7 | new-utils-class-connection |
| 8 | new-utils-from-basic |
| 9 | parse_key_value |
| 10 | rename-lenient-lowercase |
| 11 | sort-groups-to-group-sort |
| 12 | add-log-parameter-get-digest-algorithm |
| 13 | add-log-parameter-node-format |
| 14 | annotation-utils |
| 15 | autoretry-to-retry |
| 16 | combine-unpickle-task |
| 17 | dump-message-to-serialization |
| 18 | ensure_serialize |
| 19 | evaluate-promises-to-serialization |
| 20 | expand-router-string-to-utils |
| 21 | object-mro-lookup |
| 22 | rename-host-format |
| 23 | truncate-text |
| 24 | add-log-parameter-constant-time-compare |
| 25 | add-log-parameter-get-resolver |
| 26 | add-log-parameter-resolve-error-handler |
| 27 | add-none-handling-duration-string |
| 28 | combine-utils-dates-dateformat |
| 29 | combine-utils-hashable-itercompat |
| 30 | new-converter-to-python-class |
| 31 | new-path-traversal-exception |
| 32 | new-reference-context-field-class |
| 33 | new-reference-context-graph-class |
| 34 | new-timezone-class |
| 35 | new-utils-adapt-method-mode |
| 36 | new-utils-check-response |
| 37 | new-utils-path-from-module |
| 38 | remove-core-cache-utils |
| 39 | remove-db-models-constants |
| 40 | rename-file-move-safe |
| 41 | split-parse-apps-and-model-labels |
| 42 | add-log-parameter-generate-option-id-for-path |
| 43 | exception-handlers-to-handlers |
| 44 | get-auth-scheme-param |
| 45 | openapi-get-utils |
| 46 | params-to-param |
| 47 | value-is-a-sequence |
| 48 | add-log-parameter-get-debug-flag |
| 49 | add-log-parameter-get-flashed-messages |
| 50 | debughelpers-to-helpers.py |
| 51 | rename-send-from-directory |
| 52 | render-template-str |
| 53 | stream-template-str |
| 54 | add-log-parameter-get-encoding-from-headers |
| 55 | add-log-parameter-resolve-proxies |
| 56 | add-log-parameter-select-proxy |
| 57 | combine-from-key-to-key |
| 58 | combine-internal-utils-utils |
| 59 | move-hooks-sessions |
| 60 | new-cookie-utils-class |
| 61 | rename-lookup-dict-dict-lookup |
| 62 | rename-super-len-complex-len |
| 63 | split-warnings-exceptions |
| 64 | add-log-parameter-delete-directory |
| 65 | add-log-parameter-get-capability-definitions |
| 66 | add-log-parameter-recursive-diff |
| 67 | cant-create |
| 68 | channel-to-transport |
| 69 | ex-pillar-fail |
| 70 | ex-state-fail |
| 71 | exactly-n-boto-mod |
| 72 | get-unavail |
| 73 | iam-to-aws |
| 74 | mksls-to-specific |
| 75 | namecheap-xmlutil |
| 76 | paged-call-boto-mod |
| 77 | pem-fingerprint |
| 78 | perm-denied |
| 79 | add-log-parameter-disconnect-all |
| 80 | add-log-parameter-job-dir |
| 81 | add-log-parameter-xmliter |
| 82 | genspider-functions-to-utils-url |
| 83 | new-downloadermiddlewares-utils |
| 84 | new-spider-utils-in-spiders |
| 85 | new-verify-reactor-class |
| 86 | not-supported-exception-to-unsupported |
| 87 | parameterize-gunzip |
| 88 | rename-description-commands |
| 89 | rename-engine-status |
| 90 | rename-processtest-testproc |
| 91 | sitemap-url-to-url |
| 92 | global-objects |
| 93 | log-utils |
| 94 | option-parser-with-pretty-print |
| 95 | options-utils |
| 96 | remove-locale-data |
| 97 | rename-http1connection |
| 98 | rename-to-camel-case |
| 99 | resolvers-as-separate |
| 100 | tcpclient-connect-params |
| Summary |  |
| Failed | 26 |
| Timed out | 1 |
| Success rate | 73% |

---

### qwen3.6-flash S1 base+LSP RefactorBench
Source: `refbench_base_lsp_qwen36flash_s1.csv` | Rows: 100 | Columns: 21
  taskId,repo,mode,model,setup,passed,testSucceeded,applySucceeded,durationSeconds | add-log-parameter-get-group-vars,ansible_refactor,base,qwen/qwen3.6-flash,single | add-log-parameter-is-systemd-managed,ansible_refactor,base,qwen/qwen3.6-flash,si

| taskId | repo | mode | model | setup | passed | testSucceeded | applySucceeded | durationSeconds | inputTokens | outputTokens | totalTokens | requests | filesEdited | filesEditedCount | copilotExitCode | copilotTimedOut | copilotLspActionCount | copilotLspActionMarkers | applyError | completedAt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| add-log-parameter-get-group-vars | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 42.52 | 155956 | 3221 | 159177 | 9 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:48:18Z |
| add-log-parameter-is-systemd-managed | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 60.58 | 155956 | 3221 | 159177 | 9 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:49:25Z |
| combine-namespace-compat | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 63.3 | 376019 | 5663 | 381682 | 16 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:50:32Z |
| data-to-inventory-data | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 42.4 | 388542 | 4386 | 392928 | 14 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:51:16Z |
| move-quoting-splitter | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 52.66 | 213335 | 2307 | 215642 | 12 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:52:12Z |
| new-inventory-patterns | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 81.86 | 303786 | 4983 | 308769 | 13 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:53:37Z |
| new-utils-class-connection | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 87.89 | 451457 | 8789 | 460246 | 21 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:55:09Z |
| new-utils-from-basic | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 156.63 | 502223 | 7108 | 509331 | 18 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:57:48Z |
| parse_key_value | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 45.98 | 1311751 | 16360 | 1328111 | 43 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:58:37Z |
| rename-lenient-lowercase | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 23.54 | 201954 | 5537 | 207491 | 9 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:59:04Z |
| sort-groups-to-group-sort | ansible_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 25.46 | 112213 | 1930 | 114143 | 6 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:59:33Z |
| add-log-parameter-get-digest-algorithm | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 19.82 | 151949 | 1458 | 153407 | 9 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T10:59:55Z |
| add-log-parameter-node-format | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 29.73 | 67134 | 1100 | 68234 | 4 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:00:25Z |
| annotation-utils | celery_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 36.26 | 138228 | 2085 | 140313 | 7 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:01:02Z |
| autoretry-to-retry | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 68.76 | 185917 | 2360 | 188277 | 11 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:02:12Z |
| combine-unpickle-task | celery_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 44.04 | 621528 | 4924 | 626452 | 23 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:02:57Z |
| dump-message-to-serialization | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 34.25 | 273944 | 3428 | 277372 | 14 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:03:33Z |
| ensure_serialize | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 39.96 | 217436 | 2541 | 219977 | 11 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:04:14Z |
| evaluate-promises-to-serialization | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 74.55 | 303009 | 2415 | 305424 | 17 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:05:29Z |
| expand-router-string-to-utils | celery_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 56.02 | 419276 | 4700 | 423976 | 15 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:06:26Z |
| object-mro-lookup | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 23.36 | 331289 | 3537 | 334826 | 14 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:06:50Z |
| rename-host-format | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 29.63 | 128800 | 1559 | 130359 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:07:20Z |
| truncate-text | celery_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 76.55 | 143144 | 2400 | 145544 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:08:37Z |
| add-log-parameter-constant-time-compare | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | False | 188.32 | 536160 | 6482 | 542642 | 28 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover | Disallowed Copilot tool usage was detected. | 2026-05-11T11:11:54Z |
| add-log-parameter-get-resolver | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 101.9 | 1304567 | 18432 | 1322999 | 53 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:13:40Z |
| add-log-parameter-resolve-error-handler | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 30.35 | 803125 | 9210 | 812335 | 29 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:14:14Z |
| add-none-handling-duration-string | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 95.4 | 140955 | 2200 | 143155 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:15:54Z |
| combine-utils-dates-dateformat | django_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 42.84 | 187336 | 12561 | 199897 | 10 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:16:40Z |
| combine-utils-hashable-itercompat | django_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 46.45 | 254294 | 3233 | 257527 | 12 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:17:31Z |
| new-converter-to-python-class | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 50.94 | 198518 | 3402 | 201920 | 11 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:18:26Z |
| new-path-traversal-exception | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 115.08 | 248298 | 3206 | 251504 | 9 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:20:25Z |
| new-reference-context-field-class | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 67.11 | 714165 | 11793 | 725958 | 22 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:21:36Z |
| new-reference-context-graph-class | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 273.65 | 372872 | 5995 | 378867 | 16 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:26:14Z |
| new-timezone-class | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 442.2 | 3052841 | 26803 | 3079644 | 55 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:33:40Z |
| new-utils-adapt-method-mode | django_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 75.15 | 5276258 | 47035 | 5323293 | 110 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:34:59Z |
| new-utils-check-response | django_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 77.5 | 697975 | 6389 | 704364 | 24 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:36:20Z |
| new-utils-path-from-module | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 52.4 | 680777 | 5541 | 686318 | 32 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:37:16Z |
| remove-core-cache-utils | django_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 50.81 | 278771 | 4804 | 283575 | 14 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:38:11Z |
| remove-db-models-constants | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 1022.08 | 381136 | 3542 | 384678 | 18 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:55:17Z |
| rename-file-move-safe | django_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 36.34 | 2713592 | 155895 | 2869487 | 69 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:55:58Z |
| split-parse-apps-and-model-labels | django_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 32.15 | 131905 | 3700 | 135605 | 7 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:56:34Z |
| add-log-parameter-generate-option-id-for-path | fastapi_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 41.54 | 150035 | 2175 | 152210 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:57:19Z |
| exception-handlers-to-handlers | fastapi_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 101.23 | 313379 | 2989 | 316368 | 15 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T11:59:02Z |
| get-auth-scheme-param | fastapi_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 62.24 | 768626 | 8874 | 777500 | 30 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:00:06Z |
| openapi-get-utils | fastapi_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 46.61 | 448357 | 4801 | 453158 | 20 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:00:56Z |
| params-to-param | fastapi_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 64.15 | 277180 | 3175 | 280355 | 16 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:02:02Z |
| value-is-a-sequence | fastapi_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 21.37 | 454206 | 5342 | 459548 | 23 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:02:25Z |
| add-log-parameter-get-debug-flag | flask_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 80.55 | 131438 | 1050 | 132488 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:03:46Z |
| add-log-parameter-get-flashed-messages | flask_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 45.98 | 609876 | 8051 | 617927 | 32 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:04:32Z |
| debughelpers-to-helpers.py | flask_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | False | 1.1 | 368985 | 3882 | 372867 | 18 |  | 0 | 124 | True | 4 | diagnostic;find_references;go_to_definition;hover | No repository changes detected from Copilot response. | 2026-05-11T12:04:34Z |
| rename-send-from-directory | flask_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 30.44 | 368985 | 3882 | 372867 | 18 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:05:05Z |
| render-template-str | flask_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 33.72 | 115311 | 2638 | 117949 | 6 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:05:39Z |
| stream-template-str | flask_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 58.36 | 185875 | 3116 | 188991 | 9 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:06:38Z |
| add-log-parameter-get-encoding-from-headers | requests_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 54.05 | 256158 | 5947 | 262105 | 14 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:07:33Z |
| add-log-parameter-resolve-proxies | requests_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 25.54 | 371416 | 4103 | 375519 | 20 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:07:59Z |
| add-log-parameter-select-proxy | requests_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 37.8 | 136762 | 1988 | 138750 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:08:37Z |
| combine-from-key-to-key | requests_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 56.17 | 223805 | 2728 | 226533 | 12 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:09:33Z |
| combine-internal-utils-utils | requests_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 45.89 | 349047 | 6396 | 355443 | 15 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:10:20Z |
| move-hooks-sessions | requests_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 290.74 | 279046 | 4345 | 283391 | 14 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:15:11Z |
| new-cookie-utils-class | requests_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 209.27 | 1525970 | 23721 | 1549691 | 54 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:18:41Z |
| rename-lookup-dict-dict-lookup | requests_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 23.58 | 1516552 | 17894 | 1534446 | 41 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:19:05Z |
| rename-super-len-complex-len | requests_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 53.89 | 112867 | 1903 | 114770 | 6 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:19:59Z |
| split-warnings-exceptions | requests_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 209.41 | 393211 | 4391 | 397602 | 17 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:23:29Z |
| add-log-parameter-delete-directory | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 39.85 | 747492 | 24856 | 772348 | 28 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:24:15Z |
| add-log-parameter-get-capability-definitions | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 39.78 | 276547 | 2903 | 279450 | 13 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:24:58Z |
| add-log-parameter-recursive-diff | salt_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 103.05 | 227066 | 3374 | 230440 | 13 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:26:44Z |
| cant-create | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 28.18 | 593429 | 11552 | 604981 | 23 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:27:17Z |
| channel-to-transport | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 48.71 | 161952 | 1579 | 163531 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:28:09Z |
| ex-pillar-fail | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 17.58 | 358260 | 3117 | 361377 | 17 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:28:30Z |
| ex-state-fail | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 64.7 | 82003 | 622 | 82625 | 5 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:29:39Z |
| exactly-n-boto-mod | salt_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 37.87 | 478831 | 4785 | 483616 | 27 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:30:21Z |
| get-unavail | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 21.38 | 258315 | 2537 | 260852 | 10 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:30:47Z |
| iam-to-aws | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 52.23 | 102825 | 1501 | 104326 | 6 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:31:43Z |
| mksls-to-specific | salt_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | False | 9.49 | 397636 | 3994 | 401630 | 16 |  | 0 | 124 | True | 4 | diagnostic;find_references;go_to_definition;hover | No repository changes detected from Copilot response. | 2026-05-11T12:31:56Z |
| namecheap-xmlutil | salt_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 56.34 | 15479 | 240 | 15719 | 1 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:32:57Z |
| paged-call-boto-mod | salt_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 77.09 | 415898 | 5451 | 421349 | 16 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:34:18Z |
| pem-fingerprint | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 70.96 | 726132 | 5811 | 731943 | 25 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:35:33Z |
| perm-denied | salt_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 22.19 | 376573 | 8500 | 385073 | 17 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:35:59Z |
| add-log-parameter-disconnect-all | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 31.99 | 97462 | 853 | 98315 | 6 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:36:33Z |
| add-log-parameter-job-dir | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 29.56 | 143363 | 2541 | 145904 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:37:03Z |
| add-log-parameter-xmliter | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 105.84 | 142321 | 2333 | 144654 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:38:50Z |
| genspider-functions-to-utils-url | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 36.48 | 718351 | 10881 | 729232 | 28 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:39:27Z |
| new-downloadermiddlewares-utils | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 37.99 | 233588 | 2777 | 236365 | 10 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:40:06Z |
| new-spider-utils-in-spiders | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 246.6 | 181829 | 2634 | 184463 | 10 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:44:13Z |
| new-verify-reactor-class | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 120.44 | 1326061 | 14882 | 1340943 | 39 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:46:14Z |
| not-supported-exception-to-unsupported | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 49.9 | 820150 | 8857 | 829007 | 32 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:47:05Z |
| parameterize-gunzip | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 80.86 | 293082 | 4634 | 297716 | 14 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:48:26Z |
| rename-description-commands | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 79.32 | 559970 | 6009 | 565979 | 21 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:49:46Z |
| rename-engine-status | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 74.77 | 315560 | 5509 | 321069 | 10 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:51:01Z |
| rename-processtest-testproc | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 23.44 | 433042 | 8206 | 441248 | 19 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:51:25Z |
| sitemap-url-to-url | scrapy_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 48.17 | 87079 | 1994 | 89073 | 5 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:52:14Z |
| global-objects | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 35.86 | 378061 | 3750 | 381811 | 16 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:52:50Z |
| log-utils | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 138.08 | 159453 | 3103 | 162556 | 8 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:55:09Z |
| option-parser-with-pretty-print | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 121.41 | 804407 | 10170 | 814577 | 25 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T12:57:10Z |
| options-utils | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | False | False | True | 455.92 | 674561 | 15270 | 689831 | 25 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T13:04:47Z |
| remove-locale-data | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 89.58 | 1631150 | 64540 | 1695690 | 45 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T13:06:17Z |
| rename-http1connection | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 146.06 | 526407 | 7083 | 533490 | 25 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T13:08:43Z |
| rename-to-camel-case | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 33.72 | 871389 | 11502 | 882891 | 32 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T13:09:17Z |
| resolvers-as-separate | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 366.29 | 192425 | 2848 | 195273 | 10 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T13:15:24Z |
| tcpclient-connect-params | tornado_refactor | base | qwen/qwen3.6-flash | single-agent | True | True | True | 104.42 | 3252384 | 38376 | 3290760 | 93 |  | 0 | 0 | False | 4 | diagnostic;find_references;go_to_definition;hover |  | 2026-05-11T13:17:09Z |

---

### qwen3.6-flash S1 lazy+LSP RefactorBench
Source: `refbench_lazy_lsp_qwen36flash_s1.csv` | Rows: 107 | Columns: 2
  Run ID,benchmark_pipeline_20260515_155349 | Status,completed

| Model | qwen/qwen3.6-flash |
|---|---|
| Datasets | refbench |
| Setups | s1_default |
| # | Task |
| 1 | rs_1778860463373 |
| 2 | ed_1778860498915 |
| 3 | at_1778860539275 |
| 4 | ta_1778860798267 |
| 5 | er_1778860828244 |
| 6 | ns_1778860983914 |
| 7 | on_1778861059515 |
| 8 | ic_1778861104587 |
| 9 | ue_1778861171491 |
| 10 | se_1778861242195 |
| 11 | rt_1778861287405 |
| 12 | hm_1778861315619 |
| 13 | at_1778861335379 |
| 14 | ls_1778861390815 |
| 15 | ry_1778861437862 |
| 16 | sk_1778861535798 |
| 17 | on_1778861635927 |
| 18 | ze_1778861661757 |
| 19 | on_1778861716922 |
| 20 | ls_1778861766761 |
| 21 | up_1778861830847 |
| 22 | at_1778861913729 |
| 23 | xt_1778861972598 |
| 24 | re_1778862017129 |
| 25 | er_1778862149637 |
| 26 | er_1778862236215 |
| 27 | ng_1778862265536 |
| 28 | at_1778862288698 |
| 29 | at_1778862399641 |
| 30 | ss_1778862455150 |
| 31 | on_1778862499741 |
| 32 | ss_1778862636720 |
| 33 | ss_1778862767715 |
| 34 | ss_1778862801512 |
| 35 | de_1778863100377 |
| 36 | se_1778863150377 |
| 37 | le_1778863222163 |
| 38 | ls_1778863259784 |
| 39 | ts_1778863338756 |
| 40 | fe_1778863449475 |
| 41 | ls_1778863504284 |
| 42 | '-path_1778863580 |
| 43 | rs_1778863616250 |
| 44 | am_1778863663265 |
| 45 | ls_1778863709634 |
| 46 | am_1778863847838 |
| 47 | ce_1778863976652 |
| 48 | ag_1778864016607 |
| 49 | es_1778864074141 |
| 50 | py_1778864114353 |
| 51 | ry_1778864116872 |
| 52 | tr_1778864259342 |
| 53 | tr_1778864308709 |
| 54 | ders_17788643506 |
| 55 | es_1778864410172 |
| 56 | xy_1778864457390 |
| 57 | ey_1778864523069 |
| 58 | ls_1778864600551 |
| 59 | ns_1778864647485 |
| 60 | ss_1778864711121 |
| 61 | up_1778864854603 |
| 62 | en_1778864876007 |
| 63 | ns_1778864956388 |
| 64 | ry_1778865251029 |
| 65 | ns_1778865309744 |
| 66 | ff_1778865410841 |
| 67 | te_1778865495114 |
| 68 | rt_1778865522287 |
| 69 | il_1778865574711 |
| 70 | il_1778865612126 |
| 71 | od_1778865664132 |
| 72 | il_1778866050955 |
| 73 | ws_1778866074443 |
| 74 | ic_1778866132256 |
| 75 | il_1778866175444 |
| 76 | od_1778866354187 |
| 77 | nt_1778866390182 |
| 78 | ed_1778866445283 |
| 79 | ll_1778866476526 |
| 80 | ir_1778866510933 |
| 81 | er_1778866556269 |
| 82 | rl_1778866648068 |
| 83 | ls_1778866708348 |
| 84 | rs_1778866763867 |
| 85 | ss_1778866831456 |
| 86 | ed_1778866945871 |
| 87 | ip_1778866978604 |
| 88 | ds_1778867023356 |
| 89 | us_1778867099645 |
| 90 | oc_1778867140353 |
| 91 | rl_1778867174811 |
| 92 | ts_1778867234497 |
| 93 | ls_1778867331378 |
| 94 | nt_1778867640742 |
| 95 | ls_1778867712153 |
| 96 | ta_1778868088955 |
| 97 | on_1778868142187 |
| 98 | se_1778868185316 |
| 99 | te_1778868240422 |
| 100 | ms_1778868530438 |
| Summary |  |
| Failed | 50 |
| Timed out | 2 |
| Success rate | 48% |

---

### qwen3.6-flash S2-RAG descriptive RefactorBench
Source: `s2_rag_descriptive_refbench.csv` | Rows: 100 | Columns: 4

| task_id | passed | duration_seconds | rag_tool_count |
|---|---|---|---|
| add-log-parameter-get-group-vars | True | 33 |  |
| add-log-parameter-is-systemd-managed | True | 43 |  |
| combine-namespace-compat | False | 65.43 | 4 |
| data-to-inventory-data | True | 30 |  |
| move-quoting-splitter | True | 76 |  |
| new-inventory-patterns | True | 86 |  |
| new-utils-class-connection | True | 115 |  |
| new-utils-from-basic | False | 126.89 | 3 |
| parse_key_value | True | 53 |  |
| rename-lenient-lowercase | True | 40 |  |
| sort-groups-to-group-sort | True | 29 |  |
| add-log-parameter-get-digest-algorithm | True | 21 |  |
| add-log-parameter-node-format | True | 29 |  |
| annotation-utils | False | 40.83 | 3 |
| autoretry-to-retry | True | 63 |  |
| combine-unpickle-task | True | 44.77 | 3 |
| dump-message-to-serialization | True | 46 |  |
| ensure_serialize | True | 37 |  |
| evaluate-promises-to-serialization | True | 67 |  |
| expand-router-string-to-utils | True | 50.9 | 3 |
| object-mro-lookup | True | 23 |  |
| rename-host-format | True | 42 |  |
| truncate-text | True | 37 |  |
| add-log-parameter-constant-time-compare | True | 91.85 | 3 |
| add-log-parameter-get-resolver | False | 95.85 | 3 |
| add-log-parameter-resolve-error-handler | False | 56.65 | 3 |
| add-none-handling-duration-string | False | 32.97 | 3 |
| combine-utils-dates-dateformat | True | 140.45 | 3 |
| combine-utils-hashable-itercompat | True | 44 |  |
| new-converter-to-python-class | True | 77 |  |
| new-path-traversal-exception | False | 67.4 | 3 |
| new-reference-context-field-class | True | 245 |  |
| new-reference-context-graph-class | True | 111 |  |
| new-timezone-class | True | 96 |  |
| new-utils-adapt-method-mode | True | 44 |  |
| new-utils-check-response | True | 94 |  |
| new-utils-path-from-module | True | 38 |  |
| remove-core-cache-utils | True | 34 |  |
| remove-db-models-constants | True | 86 |  |
| rename-file-move-safe | True | 34 |  |
| split-parse-apps-and-model-labels | True | 55 |  |
| add-log-parameter-generate-option-id-for-path | True | 33 |  |
| exception-handlers-to-handlers | True | 52 |  |
| get-auth-scheme-param | True | 42 |  |
| openapi-get-utils | True | 48 |  |
| params-to-param | True | 87.67 | 4 |
| value-is-a-sequence | True | 23 |  |
| add-log-parameter-get-debug-flag | True | 50.86 | 3 |
| add-log-parameter-get-flashed-messages | True | 57 |  |
| debughelpers-to-helpers.py | False | 19.95 | 0 |
| rename-send-from-directory | True | 36.71 | 3 |
| render-template-str | True | 41.15 | 3 |
| stream-template-str | True | 35 |  |
| add-log-parameter-get-encoding-from-headers | True | 38 |  |
| add-log-parameter-resolve-proxies | True | 34 |  |
| add-log-parameter-select-proxy | True | 23 |  |
| combine-from-key-to-key | True | 75 |  |
| combine-internal-utils-utils | True | 59.15 | 3 |
| move-hooks-sessions | False | 332.6 | 3 |
| new-cookie-utils-class | True | 75 |  |
| rename-lookup-dict-dict-lookup | True | 29 |  |
| rename-super-len-complex-len | True | 37 |  |
| split-warnings-exceptions | True | 48 |  |
| add-log-parameter-delete-directory | True | 33 |  |
| add-log-parameter-get-capability-definitions | True | 27 |  |
| add-log-parameter-recursive-diff | True | 111 |  |
| cant-create | True | 25 |  |
| channel-to-transport | True | 66 |  |
| ex-pillar-fail | True | 27 |  |
| ex-state-fail | True | 40.45 | 3 |
| exactly-n-boto-mod | False | 44.72 | 3 |
| get-unavail | True | 31 |  |
| iam-to-aws | True | 92 |  |
| mksls-to-specific | True | 37 |  |
| namecheap-xmlutil | True | 52 |  |
| paged-call-boto-mod | False | 67.29 | 3 |
| pem-fingerprint | True | 100 |  |
| perm-denied | True | 27 |  |
| add-log-parameter-disconnect-all | True | 25 |  |
| add-log-parameter-job-dir | True | 43.19 | 3 |
| add-log-parameter-xmliter | True | 209.67 | 3 |
| genspider-functions-to-utils-url | True | 37 |  |
| new-downloadermiddlewares-utils | True | 79 |  |
| new-spider-utils-in-spiders | True | 48 |  |
| new-verify-reactor-class | True | 52 |  |
| not-supported-exception-to-unsupported | True | 46 |  |
| parameterize-gunzip | False | 73.38 | 3 |
| rename-description-commands | True | 92 |  |
| rename-engine-status | True | 106 |  |
| rename-processtest-testproc | True | 25 |  |
| sitemap-url-to-url | True | 63 |  |
| global-objects | True | 52.99 | 3 |
| log-utils | True | 106 |  |
| option-parser-with-pretty-print | False | 102.28 | 3 |
| options-utils | True | 132.99 | 3 |
| remove-locale-data | True | 52 |  |
| rename-http1connection | True | 77 |  |
| rename-to-camel-case | True | 39 |  |
| resolvers-as-separate | False | 189.96 | 3 |
| tcpclient-connect-params | True | 103.69 | 3 |

---

### qwen3.6-flash S2-RAG base RefactorBench
Source: `s2_rag_base_refbench.csv` | Rows: 100 | Columns: 4

| task_id | passed | duration_seconds | rag_tool_count |
|---|---|---|---|
| add-log-parameter-get-group-vars | True | 31.05 | 3 |
| add-log-parameter-is-systemd-managed | True | 51.08 | 3 |
| combine-namespace-compat | True | 55 |  |
| data-to-inventory-data | True | 43.28 | 4 |
| move-quoting-splitter | True | 44 |  |
| new-inventory-patterns | True | 86 |  |
| new-utils-class-connection | False | 285.13 | 3 |
| new-utils-from-basic | False | 264.99 | 3 |
| parse_key_value | True | 65.26 | 3 |
| rename-lenient-lowercase | True | 42 |  |
| sort-groups-to-group-sort | True | 34 |  |
| add-log-parameter-get-digest-algorithm | True | 25 |  |
| add-log-parameter-node-format | True | 42 |  |
| annotation-utils | False | 104.44 | 3 |
| autoretry-to-retry | True | 102 |  |
| combine-unpickle-task | True | 36 |  |
| dump-message-to-serialization | True | 34 |  |
| ensure_serialize | True | 65.94 | 3 |
| evaluate-promises-to-serialization | True | 69.08 | 3 |
| expand-router-string-to-utils | True | 112.22 | 3 |
| object-mro-lookup | True | 28.46 | 3 |
| rename-host-format | True | 67 |  |
| truncate-text | True | 56.55 | 3 |
| add-log-parameter-constant-time-compare | False | 63.68 | 3 |
| add-log-parameter-get-resolver | False | 118.24 | 4 |
| add-log-parameter-resolve-error-handler | False | 48.12 | 3 |
| add-none-handling-duration-string | True | 45 |  |
| combine-utils-dates-dateformat | True | 36.74 | 3 |
| combine-utils-hashable-itercompat | True | 51 |  |
| new-converter-to-python-class | False | 73.21 | 3 |
| new-path-traversal-exception | False | 89.64 | 4 |
| new-reference-context-field-class | True | 290.6 | 3 |
| new-reference-context-graph-class | True | 161 |  |
| new-timezone-class | True | 163 |  |
| new-utils-adapt-method-mode | True | 49 |  |
| new-utils-check-response | True | 94 |  |
| new-utils-path-from-module | True | 53.11 | 3 |
| remove-core-cache-utils | True | 64 |  |
| remove-db-models-constants | True | 125 |  |
| rename-file-move-safe | True | 56 |  |
| split-parse-apps-and-model-labels | False | 65.27 | 3 |
| add-log-parameter-generate-option-id-for-path | True | 69.27 | 3 |
| exception-handlers-to-handlers | True | 65 |  |
| get-auth-scheme-param | True | 52 |  |
| openapi-get-utils | True | 41 |  |
| params-to-param | True | 104 |  |
| value-is-a-sequence | True | 27 |  |
| add-log-parameter-get-debug-flag | True | 45 |  |
| add-log-parameter-get-flashed-messages | True | 65 |  |
| debughelpers-to-helpers.py | False | 20.12 | 0 |
| rename-send-from-directory | True | 37 |  |
| render-template-str | True | 49.53 | 3 |
| stream-template-str | False | 44.9 | 3 |
| add-log-parameter-get-encoding-from-headers | False | 52.98 | 3 |
| add-log-parameter-resolve-proxies | True | 34 |  |
| add-log-parameter-select-proxy | True | 49 |  |
| combine-from-key-to-key | False | 71.79 | 4 |
| combine-internal-utils-utils | True | 182 |  |
| move-hooks-sessions | False | 326.23 | 3 |
| new-cookie-utils-class | False | 156.2 | 3 |
| rename-lookup-dict-dict-lookup | True | 32 |  |
| rename-super-len-complex-len | True | 32 |  |
| split-warnings-exceptions | True | 58 |  |
| add-log-parameter-delete-directory | True | 67 |  |
| add-log-parameter-get-capability-definitions | True | 64 |  |
| add-log-parameter-recursive-diff | True | 197 |  |
| cant-create | True | 34 |  |
| channel-to-transport | True | 45 |  |
| ex-pillar-fail | True | 28 |  |
| ex-state-fail | True | 38 |  |
| exactly-n-boto-mod | False | 33.94 | 3 |
| get-unavail | True | 28 |  |
| iam-to-aws | True | 72 |  |
| mksls-to-specific | True | 72 |  |
| namecheap-xmlutil | True | 164 |  |
| paged-call-boto-mod | False | 44.81 | 3 |
| pem-fingerprint | True | 62 |  |
| perm-denied | True | 26 |  |
| add-log-parameter-disconnect-all | True | 33 |  |
| add-log-parameter-job-dir | True | 32 |  |
| add-log-parameter-xmliter | True | 225 |  |
| genspider-functions-to-utils-url | True | 36 |  |
| new-downloadermiddlewares-utils | False | 41.33 | 3 |
| new-spider-utils-in-spiders | False | 49.03 | 3 |
| new-verify-reactor-class | False | 102.69 | 3 |
| not-supported-exception-to-unsupported | True | 40 |  |
| parameterize-gunzip | False | 106.0 | 3 |
| rename-description-commands | True | 53 |  |
| rename-engine-status | True | 40 |  |
| rename-processtest-testproc | False | 43.06 | 3 |
| sitemap-url-to-url | True | 45 |  |
| global-objects | False | 279.15 | 3 |
| log-utils | False | 83.67 | 3 |
| option-parser-with-pretty-print | False | 72.67 | 3 |
| options-utils | True | 625.44 | 3 |
| remove-locale-data | True | 87 |  |
| rename-http1connection | True | 49 |  |
| rename-to-camel-case | True | 43 |  |
| resolvers-as-separate | False | 183.64 | 3 |
| tcpclient-connect-params | True | 91 |  |

---

### qwen3.6-flash S2-RAG lazy RefactorBench
Source: `s2_rag_lazy_refbench.csv` | Rows: 100 | Columns: 4

| task_id | passed | duration_seconds | rag_tool_count |
|---|---|---|---|
| add-log-parameter-get-group-vars | False | 45.03 | 3 |
| add-log-parameter-is-systemd-managed | True | 97.86 | 3 |
| combine-namespace-compat | True | 71.28 | 3 |
| data-to-inventory-data | True | 56 |  |
| move-quoting-splitter | False | 64.49 | 3 |
| new-inventory-patterns | True | 128.49 | 3 |
| new-utils-class-connection | True | 273.89 | 3 |
| new-utils-from-basic | False | 22.78 | 3 |
| parse_key_value | True | 56 |  |
| rename-lenient-lowercase | True | 41 |  |
| sort-groups-to-group-sort | True | 39 |  |
| add-log-parameter-get-digest-algorithm | True | 44 |  |
| add-log-parameter-node-format | False | 57.27 | 3 |
| annotation-utils | False | 36.59 | 3 |
| autoretry-to-retry | True | 59 |  |
| combine-unpickle-task | False | 49.4 | 3 |
| dump-message-to-serialization | True | 49.58 | 3 |
| ensure_serialize | True | 70 |  |
| evaluate-promises-to-serialization | True | 51 |  |
| expand-router-string-to-utils | False | 35.04 | 3 |
| object-mro-lookup | True | 34 |  |
| rename-host-format | True | 38 |  |
| truncate-text | True | 44 |  |
| add-log-parameter-constant-time-compare | False | 42.9 | 3 |
| add-log-parameter-get-resolver | False | 73.76 | 3 |
| add-log-parameter-resolve-error-handler | False | 48.9 | 3 |
| add-none-handling-duration-string | False | 33.29 | 3 |
| combine-utils-dates-dateformat | False | 45.3 | 3 |
| combine-utils-hashable-itercompat | True | 57 |  |
| new-converter-to-python-class | True | 120 |  |
| new-path-traversal-exception | False | 45.3 | 3 |
| new-reference-context-field-class | True | 300 |  |
| new-reference-context-graph-class | False | 102.43 | 3 |
| new-timezone-class | False | 17.54 | 3 |
| new-utils-adapt-method-mode | True | 57 |  |
| new-utils-check-response | True | 51 |  |
| new-utils-path-from-module | False | 102.05 | 3 |
| remove-core-cache-utils | False | 142.94 | 3 |
| remove-db-models-constants | True | 104.76 | 3 |
| rename-file-move-safe | True | 100 |  |
| split-parse-apps-and-model-labels | False | 43.0 | 3 |
| add-log-parameter-generate-option-id-for-path | False | 33.98 | 3 |
| exception-handlers-to-handlers | True | 67 |  |
| get-auth-scheme-param | True | 40 |  |
| openapi-get-utils | True | 118.4 | 3 |
| params-to-param | True | 147 |  |
| value-is-a-sequence | True | 60 |  |
| add-log-parameter-get-debug-flag | False | 75.43 | 3 |
| add-log-parameter-get-flashed-messages | False | 51.72 | 3 |
| debughelpers-to-helpers.py | False | 20.54 | 0 |
| rename-send-from-directory | False | 72.46 | 3 |
| render-template-str | False | 41.65 | 3 |
| stream-template-str | False | 56.01 | 3 |
| add-log-parameter-get-encoding-from-headers | True | 168.44 | 3 |
| add-log-parameter-resolve-proxies | True | 74 |  |
| add-log-parameter-select-proxy | True | 80.01 | 3 |
| combine-from-key-to-key | False | 71.21 | 3 |
| combine-internal-utils-utils | True | 69 |  |
| move-hooks-sessions | False | 173.14 | 3 |
| new-cookie-utils-class | False | 156.39 | 3 |
| rename-lookup-dict-dict-lookup | True | 23 |  |
| rename-super-len-complex-len | True | 50 |  |
| split-warnings-exceptions | True | 164 |  |
| add-log-parameter-delete-directory | True | 54 |  |
| add-log-parameter-get-capability-definitions | True | 49.38 | 6 |
| add-log-parameter-recursive-diff | False | 110.27 | 3 |
| cant-create | True | 29 |  |
| channel-to-transport | True | 77 |  |
| ex-pillar-fail | True | 52 |  |
| ex-state-fail | True | 50 |  |
| exactly-n-boto-mod | False | 136.66 | 3 |
| get-unavail | True | 27 |  |
| iam-to-aws | True | 63 |  |
| mksls-to-specific | False | 80.6 | 3 |
| namecheap-xmlutil | True | 82 |  |
| paged-call-boto-mod | False | 57.24 | 3 |
| pem-fingerprint | True | 53 |  |
| perm-denied | False | 34.24 | 3 |
| add-log-parameter-disconnect-all | False | 32.89 | 3 |
| add-log-parameter-job-dir | False | 57.44 | 3 |
| add-log-parameter-xmliter | True | 180 |  |
| genspider-functions-to-utils-url | False | 40.7 | 3 |
| new-downloadermiddlewares-utils | False | 64.91 | 3 |
| new-spider-utils-in-spiders | True | 75.68 | 3 |
| new-verify-reactor-class | False | 122.76 | 3 |
| not-supported-exception-to-unsupported | True | 111 |  |
| parameterize-gunzip | False | 172.62 | 3 |
| rename-description-commands | True | 92 |  |
| rename-engine-status | True | 44 |  |
| rename-processtest-testproc | True | 73 |  |
| sitemap-url-to-url | True | 58 |  |
| global-objects | False | 109.65 | 3 |
| log-utils | False | 26.49 | 3 |
| option-parser-with-pretty-print | False | 199.22 | 3 |
| options-utils | True | 362 |  |
| remove-locale-data | True | 66.03 | 3 |
| rename-http1connection | True | 56 |  |
| rename-to-camel-case | True | 73 |  |
| resolvers-as-separate | False | 165.78 | 3 |
| tcpclient-connect-params | False | 17.8 | 4 |

---

### qwen3.6-flash S3 CAO base RefactorBench
Source: `s3_cao_base_refbench.csv` | Rows: 103 | Columns: 3

| task_id | passed | duration_seconds |
|---|---|---|
| add-log-parameter-get-group-vars | True | 62 |
| add-log-parameter-is-systemd-managed | True | 98 |
| combine-namespace-compat | False | 8 |
| data-to-inventory-data | True | 65 |
| move-quoting-splitter | True | 128 |
| new-inventory-patterns | True | 194 |
| new-utils-class-connection | True | 168 |
| new-utils-from-basic | False | 234 |
| parse_key_value | True | 228 |
| rename-lenient-lowercase | True | 84 |
| sort-groups-to-group-sort | True | 67 |
| add-log-parameter-get-digest-algorithm | True | 65 |
| add-log-parameter-node-format | False | 57 |
| annotation-utils | False | 8 |
| autoretry-to-retry | True | 145 |
| combine-unpickle-task | False | 127 |
| dump-message-to-serialization | False | 22 |
| ensure_serialize | True | 99 |
| evaluate-promises-to-serialization | True | 107 |
| expand-router-string-to-utils | False | 114 |
| object-mro-lookup | True | 95 |
| rename-host-format | True | 108 |
| truncate-text | True | 108 |
| add-log-parameter-constant-time-compare | False | 226 |
| add-log-parameter-get-resolver | False | 94 |
| add-log-parameter-resolve-error-handler | False | 51 |
| add-none-handling-duration-string | True | 135 |
| combine-utils-dates-dateformat | True | 273 |
| combine-utils-hashable-itercompat | True | 132 |
| new-converter-to-python-class | False | 97 |
| new-path-traversal-exception | False | 152 |
| new-reference-context-field-class | False | 89 |
| new-reference-context-graph-class | False | 57 |
| new-timezone-class | False | 205 |
| new-utils-adapt-method-mode | False | 76 |
| new-utils-check-response | False | 7 |
| new-utils-path-from-module | False | 74 |
| remove-core-cache-utils | True | 95 |
| remove-db-models-constants | True | 167 |
| rename-file-move-safe | True | 106 |
| split-parse-apps-and-model-labels | False | 74 |
| add-log-parameter-generate-option-id-for-path | True | 141 |
| exception-handlers-to-handlers | False | 19 |
| get-auth-scheme-param | True | 70 |
| openapi-get-utils | False | 45 |
| params-to-param | True | 170 |
| value-is-a-sequence | False | 21 |
| add-log-parameter-get-debug-flag | True | 118 |
| add-log-parameter-get-flashed-messages | True | 72 |
| debughelpers-to-helpers.py | False | 2 |
| rename-send-from-directory | True | 127 |
| render-template-str | False | 114 |
| stream-template-str | False | 61 |
| add-log-parameter-get-encoding-from-headers | False | 226 |
| add-log-parameter-resolve-proxies | False | 6 |
| add-log-parameter-select-proxy | True | 124 |
| combine-from-key-to-key | True | 91 |
| combine-internal-utils-utils | True | 219 |
| move-hooks-sessions | False | 42 |
| new-cookie-utils-class | False | 541 |
| rename-lookup-dict-dict-lookup | True | 74 |
| rename-super-len-complex-len | True | 120 |
| split-warnings-exceptions | False | 11 |
| add-log-parameter-delete-directory | True | 104 |
| add-log-parameter-get-capability-definitions | True | 91 |
| add-log-parameter-recursive-diff | False | 92 |
| cant-create | True | 129 |
| channel-to-transport | True | 106 |
| ex-pillar-fail | True | 65 |
| ex-state-fail | True | 68 |
| exactly-n-boto-mod | False | 102 |
| get-unavail | True | 65 |
| iam-to-aws | False | 15 |
| mksls-to-specific | False | 6 |
| namecheap-xmlutil | False | 20 |
| paged-call-boto-mod | False | 305 |
| pem-fingerprint | False | 15 |
| perm-denied | True | 157 |
| add-log-parameter-disconnect-all | False | 19 |
| add-log-parameter-job-dir | False | 50 |
| add-log-parameter-xmliter | False | 7 |
| genspider-functions-to-utils-url | False | 10 |
| new-downloadermiddlewares-utils | False | 42 |
| new-spider-utils-in-spiders | False | 257 |
| new-verify-reactor-class | False | 40 |
| not-supported-exception-to-unsupported | True | 101 |
| parameterize-gunzip | False | 50 |
| rename-description-commands | False | 31 |
| rename-engine-status | False | 9 |
| rename-processtest-testproc | False | 52 |
| sitemap-url-to-url | False | 54 |
| global-objects | False | 6 |
| log-utils | False | 155 |
| option-parser-with-pretty-print | False | 178 |
| options-utils | True | 125 |
| remove-locale-data | False | 11 |
| rename-http1connection | True | 80 |
| rename-to-camel-case | True | 42 |
| resolvers-as-separate | True | 404 |
| tcpclient-connect-params | False | 141 |
| Summary |  |  |
| Failed | 54 |  |
| Success rate | 46% |  |

---

### qwen3.6-flash S3 subagent desc RefactorBench
Source: `s3_copilot_subagent_descriptive_refbench - crash.csv` | Rows: 103 | Columns: 3

| task_id | passed | duration_seconds |
|---|---|---|
| add-log-parameter-get-group-vars | True | 123 |
| add-log-parameter-is-systemd-managed | True | 94 |
| combine-namespace-compat | False | 262 |
| data-to-inventory-data | True | 74 |
| move-quoting-splitter | True | 144 |
| new-inventory-patterns | True | 130 |
| new-utils-class-connection | True | 248 |
| new-utils-from-basic | False | 418 |
| parse_key_value | True | 99 |
| rename-lenient-lowercase | True | 93 |
| sort-groups-to-group-sort | True | 77 |
| add-log-parameter-get-digest-algorithm | True | 44 |
| add-log-parameter-node-format | True | 55 |
| annotation-utils | False | 56 |
| autoretry-to-retry | True | 151 |
| combine-unpickle-task | True | 79 |
| dump-message-to-serialization | True | 134 |
| ensure_serialize | True | 159 |
| evaluate-promises-to-serialization | True | 222 |
| expand-router-string-to-utils | True | 39 |
| object-mro-lookup | True | 92 |
| rename-host-format | True | 71 |
| truncate-text | True | 157 |
| add-log-parameter-constant-time-compare | False | 159 |
| add-log-parameter-get-resolver | False | 160 |
| add-log-parameter-resolve-error-handler | False | 79 |
| add-none-handling-duration-string | False | 7 |
| combine-utils-dates-dateformat | False | 4 |
| combine-utils-hashable-itercompat | False | 4 |
| new-converter-to-python-class | False | 4 |
| new-path-traversal-exception | False | 4 |
| new-reference-context-field-class | False | 6 |
| new-reference-context-graph-class | False | 4 |
| new-timezone-class | False | 8 |
| new-utils-adapt-method-mode | False | 4 |
| new-utils-check-response | False | 6 |
| new-utils-path-from-module | False | 5 |
| remove-core-cache-utils | False | 8 |
| remove-db-models-constants | False | 5 |
| rename-file-move-safe | False | 9 |
| split-parse-apps-and-model-labels | False | 4 |
| add-log-parameter-generate-option-id-for-path | False | 5 |
| exception-handlers-to-handlers | False | 6 |
| get-auth-scheme-param | False | 4 |
| openapi-get-utils | False | 4 |
| params-to-param | False | 4 |
| value-is-a-sequence | False | 4 |
| add-log-parameter-get-debug-flag | False | 4 |
| add-log-parameter-get-flashed-messages | False | 4 |
| debughelpers-to-helpers.py | False | 2 |
| rename-send-from-directory | False | 4 |
| render-template-str | False | 4 |
| stream-template-str | False | 6 |
| add-log-parameter-get-encoding-from-headers | False | 4 |
| add-log-parameter-resolve-proxies | False | 5 |
| add-log-parameter-select-proxy | False | 6 |
| combine-from-key-to-key | False | 4 |
| combine-internal-utils-utils | False | 4 |
| move-hooks-sessions | False | 6 |
| new-cookie-utils-class | False | 7 |
| rename-lookup-dict-dict-lookup | False | 8 |
| rename-super-len-complex-len | False | 6 |
| split-warnings-exceptions | False | 4 |
| add-log-parameter-delete-directory | False | 5 |
| add-log-parameter-get-capability-definitions | False | 6 |
| add-log-parameter-recursive-diff | False | 6 |
| cant-create | False | 6 |
| channel-to-transport | False | 6 |
| ex-pillar-fail | False | 6 |
| ex-state-fail | False | 4 |
| exactly-n-boto-mod | False | 4 |
| get-unavail | False | 4 |
| iam-to-aws | False | 4 |
| mksls-to-specific | False | 4 |
| namecheap-xmlutil | False | 4 |
| paged-call-boto-mod | False | 4 |
| pem-fingerprint | False | 4 |
| perm-denied | False | 4 |
| add-log-parameter-disconnect-all | False | 4 |
| add-log-parameter-job-dir | False | 4 |
| add-log-parameter-xmliter | False | 4 |
| genspider-functions-to-utils-url | False | 4 |
| new-downloadermiddlewares-utils | False | 4 |
| new-spider-utils-in-spiders | False | 4 |
| new-verify-reactor-class | False | 4 |
| not-supported-exception-to-unsupported | False | 4 |
| parameterize-gunzip | False | 7 |
| rename-description-commands | False | 4 |
| rename-engine-status | False | 4 |
| rename-processtest-testproc | False | 4 |
| sitemap-url-to-url | False | 4 |
| global-objects | False | 4 |
| log-utils | False | 4 |
| option-parser-with-pretty-print | False | 4 |
| options-utils | False | 4 |
| remove-locale-data | False | 4 |
| rename-http1connection | False | 4 |
| rename-to-camel-case | False | 4 |
| resolvers-as-separate | False | 4 |
| tcpclient-connect-params | False | 4 |
| Summary |  |  |
| Failed | 80 |  |
| Success rate | 77% (20/26 executed) |  |

---


---


---


---

### openrouter/free S3 multi-agent RefactorBench
Source: `benchmark_pipeline_20260605_101747_monitor_exact_export_20260605184052.csv` | Rows: 100 | Columns: 20
  Run ID,benchmark_pipeline_20260605_101747 | Status,completed | Model,openrouter/free

| Nr | Task | Status | Input | Output | Cache | Time | Evals | Cmpct | Reqs | +Lines | -Lines | Files | Model | Build/Test | Model mismatch | Result | Checks | Reason | Build Log |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | add-log-parameter-get-group-vars | terminated | 406.1k | 5.6k | 270 | 5m20s | 0 | 0 | 22 | 12 | 2 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 2 | add-log-parameter-is-systemd-managed | terminated | 289.5k | 4.0k | 6.8k | 2m08s | 0 | 0 | 15 | 4 | 4 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 3 | combine-namespace-compat | completed | 621.2k | 16.5k | 97.4k | 6m44s | 0 | 0 | 30 | 18 | 4 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 4 | data-to-inventory-data | completed | 189.7k | 1.8k | 24.9k | 1m15s | 0 | 0 | 11 | '- | '- | '- | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 5 | move-quoting-splitter | terminated | 439.3k | 4.6k | 68.3k | 6m10s | 0 | 0 | 25 | '- | '- | '- | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 6 | new-inventory-patterns | completed | 340.3k | 15.7k | 135 | 3m07s | 0 | 0 | 18 | 101 | 72 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 7 | new-utils-class-connection | terminated | 876.1k | 23.8k | 33.6k | 6m24s | 0 | 0 | 35 | 51 | 51 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 8 | new-utils-from-basic | terminated | 977.7k | 7.9k | 149.3k | 4m33s | 0 | 0 | 40 | 97 | 6 | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 9 | parse_key_value | terminated | 405.7k | 6.1k | 21.2k | 4m20s | 0 | 0 | 21 | 4 | 4 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 10 | rename-lenient-lowercase | completed | 380.0k | 5.6k | 6.7k | 2m56s | 0 | 0 | 20 | 3 | 3 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 11 | sort-groups-to-group-sort | terminated | 688.1k | 6.3k | 35.5k | 4m02s | 0 | 0 | 36 | 4 | 4 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 12 | add-log-parameter-get-digest-algorithm | terminated | 231.6k | 3.9k | 13.6k | 3m13s | 0 | 0 | 14 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 13 | add-log-parameter-node-format | terminated | 330.4k | 2.7k | 23.1k | 1m55s | 0 | 0 | 19 | 5 | 5 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 14 | annotation-utils | completed | 226.7k | 4.0k | 8.1k | 2m17s | 0 | 0 | 14 | 12 | 1 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 15 | autoretry-to-retry | terminated | 1.0M | 7.1k | 59.4k | 5m51s | 0 | 0 | 45 | 14 | 3 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 16 | combine-unpickle-task | completed | 1.2M | 5.8k | 131.3k | 5m35s | 0 | 0 | 48 | 10 | 13 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 17 | dump-message-to-serialization | terminated | 219.6k | 2.1k | 8.1k | 1m51s | 0 | 0 | 11 | 10 | 9 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 18 | ensure_serialize | terminated | 424.4k | 2.4k | 60.0k | 2m18s | 0 | 0 | 18 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 19 | evaluate-promises-to-serialization | terminated | 970.9k | 15.2k | 23.2k | 5m52s | 0 | 0 | 28 | 4 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 20 | expand-router-string-to-utils | completed | 254.9k | 5.7k | 78 | 3m18s | 0 | 0 | 12 | 17 | '- | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 21 | object-mro-lookup | terminated | 145.0k | 2.0k | 31.0k | 46s | 0 | 0 | 9 | 2 | 1 | 1 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 22 | rename-host-format | completed | 380.4k | 2.5k | 23.6k | 1m33s | 0 | 0 | 16 | 5 | 5 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 23 | truncate-text | terminated | 713.9k | 12.3k | 46.0k | 5m45s | 0 | 0 | 28 | 10 | 10 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 24 | add-log-parameter-constant-time-compare | terminated | 30.7k | 931 | '- | 38s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 25 | add-log-parameter-get-resolver | terminated | 31.5k | 433 | '- | 5s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 26 | add-log-parameter-resolve-error-handler | terminated | 436.0k | 7.7k | 17.3k | 4m58s | 0 | 0 | 24 | 5 | 5 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 27 | add-none-handling-duration-string | completed | 248.6k | 1.8k | 38.2k | 2m01s | 0 | 0 | 15 | 2 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 28 | combine-utils-dates-dateformat | completed | 469.4k | 4.9k | 45.4k | 3m38s | 0 | 0 | 21 | 77 | 10 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 29 | combine-utils-hashable-itercompat | completed | 477.5k | 7.4k | 38.6k | 4m39s | 0 | 0 | 26 | 92 | '- | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 30 | new-converter-to-python-class | terminated | 708.3k | 13.7k | 100.9k | 6m18s | 0 | 0 | 25 | 55 | '- | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 31 | new-path-traversal-exception | terminated | 540.3k | 26.2k | 47.7k | 5m32s | 0 | 0 | 24 | 9 | 3 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 32 | new-reference-context-field-class | terminated | 597.8k | 9.8k | 44.0k | 7m06s | 0 | 0 | 24 | 128 | 105 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 33 | new-reference-context-graph-class | terminated | 608.8k | 31.8k | 27.1k | 7m26s | 0 | 0 | 26 | 24 | 11 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 34 | new-timezone-class | completed | 216.4k | 1.7k | 235 | 1m53s | 0 | 0 | 12 | '- | '- | '- | yes | checked | no | FAILED | code=no build=no ast=- verified=no | test_failed |  |
| 35 | new-utils-adapt-method-mode | completed | 354.4k | 7.0k | 45.7k | 5m29s | 0 | 0 | 17 | 35 | 35 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 36 | new-utils-check-response | completed | 190.2k | 2.2k | 78 | 2m04s | 0 | 0 | 10 | 30 | '- | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 37 | new-utils-path-from-module | terminated | 152.3k | 2.9k | 128 | 1m39s | 0 | 0 | 9 | 31 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 38 | remove-core-cache-utils | completed | 295.1k | 6.8k | 18.2k | 4m35s | 0 | 0 | 16 | 19 | 9 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 39 | remove-db-models-constants | terminated | 391.0k | 9.1k | 40.5k | 4m15s | 0 | 0 | 22 | 14 | 6 | 6 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 40 | rename-file-move-safe | terminated | 724.3k | 9.2k | 43.8k | 6m43s | 0 | 0 | 29 | 10 | 10 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 41 | split-parse-apps-and-model-labels | completed | 177.4k | 3.4k | 142 | 2m17s | 0 | 0 | 10 | 11 | 12 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 42 | add-log-parameter-generate-option-id-for-path | terminated | 28.4k | 139 | 128 | 11s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 43 | exception-handlers-to-handlers | terminated | 536.5k | 4.7k | 34.8k | 4m05s | 0 | 0 | 26 | 4 | 4 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 44 | get-auth-scheme-param | terminated | 565.1k | 10.3k | 40.2k | 6m25s | 0 | 0 | 31 | 2 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 45 | openapi-get-utils | completed | 125.4k | 1.4k | 8.1k | 1m46s | 0 | 0 | 8 | 6 | 6 | 6 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 46 | params-to-param | terminated | 529.2k | 7.2k | 76.8k | 4m53s | 0 | 0 | 25 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 47 | value-is-a-sequence | terminated | 385.5k | 3.9k | 35.0k | 2m57s | 0 | 0 | 21 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 48 | add-log-parameter-get-debug-flag | completed | 498.9k | 8.5k | 80.3k | 7m09s | 0 | 0 | 28 | 6 | 5 | 4 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 49 | add-log-parameter-get-flashed-messages | terminated | 1.6M | 22.8k | 198.9k | 16m31s | 0 | 0 | 59 | 8 | 7 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 50 | debughelpers-to-helpers.py | terminated | 1.6M | 22.8k | 198.9k | 16m31s | 0 | 0 | 59 | 8 | 7 | 2 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 51 | rename-send-from-directory | completed | 633.3k | 3.8k | 8.1k | 5m24s | 0 | 0 | 27 | 6 | 6 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 52 | render-template-str | terminated | 552.7k | 5.9k | 313 | 5m39s | 0 | 0 | 25 | 8 | 8 | 4 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 53 | stream-template-str | completed | 403.7k | 10.0k | 25.6k | 4m33s | 0 | 0 | 21 | 5 | 4 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 54 | add-log-parameter-get-encoding-from-headers | completed | 263.3k | 5.9k | 71 | 4m12s | 0 | 0 | 16 | 2 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 55 | add-log-parameter-resolve-proxies | terminated | 199.1k | 3.0k | 8.1k | 2m31s | 0 | 0 | 12 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 56 | add-log-parameter-select-proxy | completed | 321.7k | 5.8k | 55.9k | 2m59s | 0 | 0 | 20 | 4 | 4 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 57 | combine-from-key-to-key | terminated | 282.7k | 3.7k | 208 | 3m07s | 0 | 0 | 16 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 58 | combine-internal-utils-utils | completed | 651.5k | 10.0k | 87.2k | 6m08s | 0 | 0 | 32 | 46 | 11 | 5 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 59 | move-hooks-sessions | terminated | 1.4M | 27.6k | 28.4k | 22m01s | 0 | 0 | 57 | 51 | 23 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 60 | new-cookie-utils-class | terminated | 251.8k | 4.5k | 152 | 2m12s | 0 | 0 | 13 | 44 | '- | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 61 | rename-lookup-dict-dict-lookup | completed | 252.3k | 2.5k | 107 | 3m03s | 0 | 0 | 14 | 6 | 6 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 62 | rename-super-len-complex-len | completed | 341.5k | 3.1k | 24.6k | 3m59s | 0 | 0 | 20 | 3 | 2 | 2 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 63 | split-warnings-exceptions | completed | 716.9k | 23.2k | 19.9k | 8m33s | 0 | 0 | 34 | 21 | 19 | 3 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 64 | add-log-parameter-delete-directory | completed | 626.7k | 6.1k | 47.0k | 5m11s | 0 | 0 | 25 | 2 | 2 | 2 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 65 | add-log-parameter-get-capability-definitions | completed | 266.9k | 1.5k | 259 | 3m13s | 0 | 0 | 14 | 3 | 3 | 3 | yes | checked | no | PASSED | code=yes build=yes ast=- verified=yes |  |  |
| 66 | add-log-parameter-recursive-diff | terminated | 347.4k | 8.4k | 20.5k | 4m04s | 0 | 0 | 18 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 67 | cant-create | terminated | 26.8k | 148 | 128 | 21s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 68 | channel-to-transport | terminated | 12.4k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 69 | ex-pillar-fail | terminated | 13.3k | 62 | 64 | 4s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 70 | ex-state-fail | terminated | 12.4k | '- | '- | 14s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 71 | exactly-n-boto-mod | terminated | 100.0k | 716 | 27.2k | 1m02s | 0 | 0 | 8 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 72 | get-unavail | terminated | 26.9k | 94 | 13.3k | 7s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 73 | iam-to-aws | terminated | 13.2k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 74 | mksls-to-specific | terminated | 12.4k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 75 | namecheap-xmlutil | terminated | 13.2k | '- | '- | 8s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 76 | paged-call-boto-mod | terminated | 13.3k | 56 | 64 | 3s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 77 | pem-fingerprint | terminated | 55.6k | 442 | 272 | 35s | 0 | 0 | 4 | 1 | 1 | 1 | yes | checked | no | FAILED | code=yes build=no ast=- verified=no | test_failed |  |
| 78 | perm-denied | terminated | 68.7k | 372 | 20.2k | 28s | 0 | 0 | 5 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 79 | add-log-parameter-disconnect-all | terminated | 46.4k | 231 | 29.8k | 13s | 0 | 0 | 3 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 80 | add-log-parameter-job-dir | terminated | 13.2k | '- | '- | 7s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 81 | add-log-parameter-xmliter | terminated | 26.8k | 123 | 128 | 10s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 82 | genspider-functions-to-utils-url | terminated | 13.3k | 65 | 64 | 3s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 83 | new-downloadermiddlewares-utils | terminated | 13.2k | '- | '- | 7s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 84 | new-spider-utils-in-spiders | terminated | 26.8k | 149 | 128 | 9s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 85 | new-verify-reactor-class | terminated | 13.2k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 86 | not-supported-exception-to-unsupported | terminated | 13.3k | 58 | 64 | 3s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 87 | parameterize-gunzip | terminated | 13.2k | '- | '- | 7s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 88 | rename-description-commands | terminated | 13.2k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 89 | rename-engine-status | terminated | 13.3k | 62 | 64 | 4s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 90 | rename-processtest-testproc | terminated | 13.2k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 91 | sitemap-url-to-url | terminated | 13.2k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 92 | global-objects | terminated | 91.4k | 490 | 58.2k | 31s | 0 | 0 | 7 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 93 | log-utils | terminated | 13.2k | '- | '- | 7s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 94 | option-parser-with-pretty-print | terminated | 13.3k | 52 | 64 | 12s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 95 | options-utils | terminated | 13.2k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 96 | remove-locale-data | terminated | 26.9k | 160 | 128 | 12s | 0 | 0 | 2 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 97 | rename-http1connection | terminated | 13.2k | '- | '- | 4s | 0 | 0 | 0 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 98 | rename-to-camel-case | terminated | 57.9k | 324 | 29.1k | 19s | 0 | 0 | 4 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 99 | resolvers-as-separate | terminated | 13.3k | 80 | 64 | 4s | 0 | 0 | 1 | '- | '- | '- | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
| 100 | tcpclient-connect-params | terminated | 62.5k | 504 | 17.9k | 24s | 0 | 0 | 4 | 6 | '- | 1 | yes | checked | no | TIMEOUT | code=no build=no ast=- verified=no | test_failed |  |
---

### deepseek-v4-pro S2-RAG descriptive RefactorBench
Model: deepseek-v4-pro | Setup: S2-RAG (AST) descriptive | Tasks: 100 | Passed: 89/100

| Nr | Repo | TaskId | Passed | TestSucceeded | ApplySucceeded | Duration(s) |
|---|------|--------|--------|---------------|----------------|-------------|
| 1 | ansible_refactor | add-log-parameter-get-group-vars | True | True | True | 201.9 |
| 2 | ansible_refactor | add-log-parameter-is-systemd-managed | True | True | True | 156.8 |
| 3 | ansible_refactor | combine-namespace-compat | True | True | True | 211.8 |
| 4 | ansible_refactor | data-to-inventory-data | True | True | True | 149.3 |
| 5 | ansible_refactor | move-quoting-splitter | True | True | True | 193.8 |
| 6 | ansible_refactor | new-inventory-patterns | True | True | True | 347.2 |
| 7 | ansible_refactor | new-utils-class-connection | True | True | True | 209.2 |
| 8 | ansible_refactor | new-utils-from-basic | False | False | True | 387.6 |
| 9 | ansible_refactor | parse_key_value | True | True | True | 345.6 |
| 10 | ansible_refactor | rename-lenient-lowercase | True | True | True | 231.7 |
| 11 | ansible_refactor | sort-groups-to-group-sort | True | True | True | 111.0 |
| 12 | celery_refactor | add-log-parameter-get-digest-algorithm | True | True | True | 103.2 |
| 13 | celery_refactor | add-log-parameter-node-format | True | True | True | 128.0 |
| 14 | celery_refactor | annotation-utils | True | True | True | 165.0 |
| 15 | celery_refactor | autoretry-to-retry | True | True | True | 186.6 |
| 16 | celery_refactor | combine-unpickle-task | True | True | True | 133.7 |
| 17 | celery_refactor | dump-message-to-serialization | True | True | True | 130.4 |
| 18 | celery_refactor | ensure_serialize | True | True | True | 152.5 |
| 19 | celery_refactor | evaluate-promises-to-serialization | True | True | True | 217.5 |
| 20 | celery_refactor | expand-router-string-to-utils | True | True | True | 166.3 |
| 21 | celery_refactor | object-mro-lookup | True | True | True | 84.9 |
| 22 | celery_refactor | rename-host-format | True | True | True | 111.5 |
| 23 | celery_refactor | truncate-text | True | True | True | 143.5 |
| 24 | django_refactor | add-log-parameter-constant-time-compare | True | True | True | 209.9 |
| 25 | django_refactor | add-log-parameter-get-resolver | False | False | True | 262.9 |
| 26 | django_refactor | add-log-parameter-resolve-error-handler | False | False | True | 205.6 |
| 27 | django_refactor | add-none-handling-duration-string | True | True | True | 184.2 |
| 28 | django_refactor | combine-utils-dates-dateformat | True | True | True | 226.5 |
| 29 | django_refactor | combine-utils-hashable-itercompat | True | True | True | 157.7 |
| 30 | django_refactor | new-converter-to-python-class | True | True | True | 224.2 |
| 31 | django_refactor | new-path-traversal-exception | False | False | True | 857.2 |
| 32 | django_refactor | new-reference-context-field-class | False | False | True | 388.4 |
| 33 | django_refactor | new-reference-context-graph-class | True | True | True | 622.0 |
| 34 | django_refactor | new-timezone-class | True | True | True | 181.1 |
| 35 | django_refactor | new-utils-adapt-method-mode | True | True | True | 245.2 |
| 36 | django_refactor | new-utils-check-response | True | True | True | 240.3 |
| 37 | django_refactor | new-utils-path-from-module | True | True | True | 138.2 |
| 38 | django_refactor | remove-core-cache-utils | True | True | True | 173.1 |
| 39 | django_refactor | remove-db-models-constants | True | True | True | 297.7 |
| 40 | django_refactor | rename-file-move-safe | True | True | True | 194.7 |
| 41 | django_refactor | split-parse-apps-and-model-labels | True | True | True | 171.3 |
| 42 | fastapi_refactor | add-log-parameter-generate-option-id-for-path | True | True | True | 155.8 |
| 43 | fastapi_refactor | exception-handlers-to-handlers | True | True | True | 130.7 |
| 44 | fastapi_refactor | get-auth-scheme-param | True | True | True | 206.7 |
| 45 | fastapi_refactor | openapi-get-utils | True | True | True | 221.5 |
| 46 | fastapi_refactor | params-to-param | False | False | True | 461.6 |
| 47 | fastapi_refactor | value-is-a-sequence | True | True | True | 191.7 |
| 48 | flask_refactor | add-log-parameter-get-debug-flag | True | True | True | 174.5 |
| 49 | flask_refactor | add-log-parameter-get-flashed-messages | True | True | True | 114.3 |
| 50 | flask_refactor | debughelpers-to-helpers.py | True | True | False | 27.2 |
| 51 | flask_refactor | rename-send-from-directory | True | True | True | 179.0 |
| 52 | flask_refactor | render-template-str | True | True | True | 248.1 |
| 53 | flask_refactor | stream-template-str | True | True | True | 131.5 |
| 54 | requests_refactor | add-log-parameter-get-encoding-from-headers | True | True | True | 124.5 |
| 55 | requests_refactor | add-log-parameter-resolve-proxies | True | True | True | 112.1 |
| 56 | requests_refactor | add-log-parameter-select-proxy | True | True | True | 134.7 |
| 57 | requests_refactor | combine-from-key-to-key | True | True | True | 319.3 |
| 58 | requests_refactor | combine-internal-utils-utils | True | True | True | 545.7 |
| 59 | requests_refactor | move-hooks-sessions | True | True | True | 475.6 |
| 60 | requests_refactor | new-cookie-utils-class | True | True | True | 371.9 |
| 61 | requests_refactor | rename-lookup-dict-dict-lookup | True | True | True | 138.0 |
| 62 | requests_refactor | rename-super-len-complex-len | True | True | True | 225.7 |
| 63 | requests_refactor | split-warnings-exceptions | True | True | True | 895.9 |
| 64 | salt_refactor | add-log-parameter-delete-directory | True | True | True | 209.8 |
| 65 | salt_refactor | add-log-parameter-get-capability-definitions | True | True | True | 122.4 |
| 66 | salt_refactor | add-log-parameter-recursive-diff | True | True | True | 417.3 |
| 67 | salt_refactor | cant-create | True | True | True | 115.4 |
| 68 | salt_refactor | channel-to-transport | True | True | True | 154.7 |
| 69 | salt_refactor | ex-pillar-fail | True | True | True | 136.6 |
| 70 | salt_refactor | ex-state-fail | True | True | True | 173.7 |
| 71 | salt_refactor | exactly-n-boto-mod | True | True | True | 212.0 |
| 72 | salt_refactor | get-unavail | True | True | True | 125.5 |
| 73 | salt_refactor | iam-to-aws | True | True | True | 119.1 |
| 74 | salt_refactor | mksls-to-specific | True | True | True | 103.8 |
| 75 | salt_refactor | namecheap-xmlutil | True | True | True | 282.0 |
| 76 | salt_refactor | paged-call-boto-mod | True | True | True | 185.9 |
| 77 | salt_refactor | pem-fingerprint | True | True | True | 237.4 |
| 78 | salt_refactor | perm-denied | True | True | True | 184.6 |
| 79 | scrapy_refactor | add-log-parameter-disconnect-all | True | True | True | 137.8 |
| 80 | scrapy_refactor | add-log-parameter-job-dir | True | True | True | 189.2 |
| 81 | scrapy_refactor | add-log-parameter-xmliter | True | True | True | 172.8 |
| 82 | scrapy_refactor | genspider-functions-to-utils-url | True | True | True | 135.4 |
| 83 | scrapy_refactor | new-downloadermiddlewares-utils | True | True | True | 197.9 |
| 84 | scrapy_refactor | new-spider-utils-in-spiders | True | True | True | 334.4 |
| 85 | scrapy_refactor | new-verify-reactor-class | True | True | True | 202.4 |
| 86 | scrapy_refactor | not-supported-exception-to-unsupported | True | True | True | 171.4 |
| 87 | scrapy_refactor | parameterize-gunzip | False | False | True | 260.9 |
| 88 | scrapy_refactor | rename-description-commands | True | True | True | 192.1 |
| 89 | scrapy_refactor | rename-engine-status | True | True | True | 175.5 |
| 90 | scrapy_refactor | rename-processtest-testproc | True | True | True | 170.4 |
| 91 | scrapy_refactor | sitemap-url-to-url | True | True | True | 302.6 |
| 92 | tornado_refactor | global-objects | True | True | True | 508.0 |
| 93 | tornado_refactor | log-utils | False | False | True | 288.1 |
| 94 | tornado_refactor | option-parser-with-pretty-print | False | False | True | 804.4 |
| 95 | tornado_refactor | options-utils | True | True | True | 916.2 |
| 96 | tornado_refactor | remove-locale-data | True | True | True | 146.4 |
| 97 | tornado_refactor | rename-http1connection | True | True | True | 125.7 |
| 98 | tornado_refactor | rename-to-camel-case | True | True | True | 204.0 |
| 99 | tornado_refactor | resolvers-as-separate | False | False | True | 773.3 |
| 100 | tornado_refactor | tcpclient-connect-params | False | False | True | 596.3 |

---

### minimax-m3 S2-RAG descriptive RefactorBench
Model: minimax-m3 | Setup: S2-RAG (AST) descriptive | Tasks: 100 | Passed: 81/100

| Nr | Repo | TaskId | Passed | TestSucceeded | ApplySucceeded | Duration(s) |
|---|------|--------|--------|---------------|----------------|-------------|
| 1 | ansible_refactor | add-log-parameter-get-group-vars | True | True | True | 147.1 |
| 2 | ansible_refactor | add-log-parameter-is-systemd-managed | True | True | True | 110.9 |
| 3 | ansible_refactor | combine-namespace-compat | True | True | True | 271.9 |
| 4 | ansible_refactor | data-to-inventory-data | True | True | True | 74.8 |
| 5 | ansible_refactor | move-quoting-splitter | True | True | True | 166.8 |
| 6 | ansible_refactor | new-inventory-patterns | True | True | True | 252.7 |
| 7 | ansible_refactor | new-utils-class-connection | True | True | True | 261.3 |
| 8 | ansible_refactor | new-utils-from-basic | False | False | True | 491.0 |
| 9 | ansible_refactor | parse_key_value | True | True | True | 290.5 |
| 10 | ansible_refactor | rename-lenient-lowercase | True | True | True | 185.2 |
| 11 | ansible_refactor | sort-groups-to-group-sort | True | True | True | 98.8 |
| 12 | celery_refactor | add-log-parameter-get-digest-algorithm | True | True | True | 129.1 |
| 13 | celery_refactor | add-log-parameter-node-format | True | True | True | 98.3 |
| 14 | celery_refactor | annotation-utils | False | False | True | 167.0 |
| 15 | celery_refactor | autoretry-to-retry | True | True | True | 164.2 |
| 16 | celery_refactor | combine-unpickle-task | True | True | True | 140.8 |
| 17 | celery_refactor | dump-message-to-serialization | True | True | True | 174.9 |
| 18 | celery_refactor | ensure_serialize | True | True | True | 185.3 |
| 19 | celery_refactor | evaluate-promises-to-serialization | True | True | True | 218.9 |
| 20 | celery_refactor | expand-router-string-to-utils | True | True | True | 178.1 |
| 21 | celery_refactor | object-mro-lookup | True | True | True | 82.5 |
| 22 | celery_refactor | rename-host-format | True | True | True | 123.8 |
| 23 | celery_refactor | truncate-text | True | True | True | 207.7 |
| 24 | django_refactor | add-log-parameter-constant-time-compare | True | True | True | 186.7 |
| 25 | django_refactor | add-log-parameter-get-resolver | False | False | True | 162.9 |
| 26 | django_refactor | add-log-parameter-resolve-error-handler | False | False | True | 244.3 |
| 27 | django_refactor | add-none-handling-duration-string | False | False | True | 147.2 |
| 28 | django_refactor | combine-utils-dates-dateformat | True | True | True | 244.2 |
| 29 | django_refactor | combine-utils-hashable-itercompat | True | True | True | 157.8 |
| 30 | django_refactor | new-converter-to-python-class | True | True | True | 462.9 |
| 31 | django_refactor | new-path-traversal-exception | False | False | True | 743.9 |
| 32 | django_refactor | new-reference-context-field-class | True | True | True | 308.8 |
| 33 | django_refactor | new-reference-context-graph-class | True | True | True | 352.7 |
| 34 | django_refactor | new-timezone-class | True | True | True | 140.4 |
| 35 | django_refactor | new-utils-adapt-method-mode | True | True | True | 197.7 |
| 36 | django_refactor | new-utils-check-response | True | True | True | 167.0 |
| 37 | django_refactor | new-utils-path-from-module | True | True | True | 153.8 |
| 38 | django_refactor | remove-core-cache-utils | False | False | True | 170.3 |
| 39 | django_refactor | remove-db-models-constants | False | False | False | 1662.3 |
| 40 | django_refactor | rename-file-move-safe | True | True | True | 187.3 |
| 41 | django_refactor | split-parse-apps-and-model-labels | True | True | True | 119.0 |
| 42 | fastapi_refactor | add-log-parameter-generate-option-id-for-path | True | True | True | 122.5 |
| 43 | fastapi_refactor | exception-handlers-to-handlers | True | True | True | 354.7 |
| 44 | fastapi_refactor | get-auth-scheme-param | True | True | True | 176.7 |
| 45 | fastapi_refactor | openapi-get-utils | True | True | True | 169.8 |
| 46 | fastapi_refactor | params-to-param | True | True | True | 409.5 |
| 47 | fastapi_refactor | value-is-a-sequence | True | True | True | 164.2 |
| 48 | flask_refactor | add-log-parameter-get-debug-flag | True | True | True | 186.5 |
| 49 | flask_refactor | add-log-parameter-get-flashed-messages | True | True | True | 175.5 |
| 50 | flask_refactor | debughelpers-to-helpers.py | False | False | False | 25.6 |
| 51 | flask_refactor | rename-send-from-directory | False | False | True | 357.8 |
| 52 | flask_refactor | render-template-str | True | True | True | 175.2 |
| 53 | flask_refactor | stream-template-str | True | True | True | 75.6 |
| 54 | requests_refactor | add-log-parameter-get-encoding-from-headers | True | True | True | 225.4 |
| 55 | requests_refactor | add-log-parameter-resolve-proxies | True | True | True | 75.8 |
| 56 | requests_refactor | add-log-parameter-select-proxy | True | True | True | 85.6 |
| 57 | requests_refactor | combine-from-key-to-key | True | True | True | 168.5 |
| 58 | requests_refactor | combine-internal-utils-utils | True | True | True | 346.9 |
| 59 | requests_refactor | move-hooks-sessions | True | True | True | 571.3 |
| 60 | requests_refactor | new-cookie-utils-class | True | True | True | 385.1 |
| 61 | requests_refactor | rename-lookup-dict-dict-lookup | True | True | True | 93.2 |
| 62 | requests_refactor | rename-super-len-complex-len | True | True | True | 214.3 |
| 63 | requests_refactor | split-warnings-exceptions | True | True | True | 976.5 |
| 64 | salt_refactor | add-log-parameter-delete-directory | True | True | True | 184.3 |
| 65 | salt_refactor | add-log-parameter-get-capability-definitions | True | True | True | 134.6 |
| 66 | salt_refactor | add-log-parameter-recursive-diff | True | True | True | 233.4 |
| 67 | salt_refactor | cant-create | True | True | True | 83.3 |
| 68 | salt_refactor | channel-to-transport | True | True | True | 134.3 |
| 69 | salt_refactor | ex-pillar-fail | True | True | True | 101.0 |
| 70 | salt_refactor | ex-state-fail | True | True | True | 124.3 |
| 71 | salt_refactor | exactly-n-boto-mod | True | True | True | 187.8 |
| 72 | salt_refactor | get-unavail | True | True | True | 140.7 |
| 73 | salt_refactor | iam-to-aws | True | True | True | 146.5 |
| 74 | salt_refactor | mksls-to-specific | True | True | True | 139.0 |
| 75 | salt_refactor | namecheap-xmlutil | True | True | True | 220.7 |
| 76 | salt_refactor | paged-call-boto-mod | True | True | True | 284.5 |
| 77 | salt_refactor | pem-fingerprint | False | False | True | 175.8 |
| 78 | salt_refactor | perm-denied | True | True | True | 101.9 |
| 79 | scrapy_refactor | add-log-parameter-disconnect-all | True | True | True | 89.5 |
| 80 | scrapy_refactor | add-log-parameter-job-dir | True | True | True | 126.3 |
| 81 | scrapy_refactor | add-log-parameter-xmliter | True | True | True | 1089.2 |
| 82 | scrapy_refactor | genspider-functions-to-utils-url | True | True | True | 139.4 |
| 83 | scrapy_refactor | new-downloadermiddlewares-utils | True | True | True | 121.0 |
| 84 | scrapy_refactor | new-spider-utils-in-spiders | True | True | True | 251.3 |
| 85 | scrapy_refactor | new-verify-reactor-class | True | True | True | 170.2 |
| 86 | scrapy_refactor | not-supported-exception-to-unsupported | True | True | True | 155.1 |
| 87 | scrapy_refactor | parameterize-gunzip | False | False | True | 263.1 |
| 88 | scrapy_refactor | rename-description-commands | True | True | True | 72.4 |
| 89 | scrapy_refactor | rename-engine-status | True | True | True | 136.6 |
| 90 | scrapy_refactor | rename-processtest-testproc | True | True | True | 94.9 |
| 91 | scrapy_refactor | sitemap-url-to-url | True | True | True | 207.7 |
| 92 | tornado_refactor | global-objects | True | True | True | 322.8 |
| 93 | tornado_refactor | log-utils | False | False | True | 181.8 |
| 94 | tornado_refactor | option-parser-with-pretty-print | False | False | True | 425.2 |
| 95 | tornado_refactor | options-utils | True | True | True | 854.0 |
| 96 | tornado_refactor | remove-locale-data | False | False | True | 111.6 |
| 97 | tornado_refactor | rename-http1connection | False | False | True | 206.6 |
| 98 | tornado_refactor | rename-to-camel-case | False | False | True | 198.8 |
| 99 | tornado_refactor | resolvers-as-separate | False | False | True | 516.2 |
| 100 | tornado_refactor | tcpclient-connect-params | False | False | True | 256.3 |

---

### kimi-k2.6 S2-RAG descriptive RefactorBench
Model: kimi-k2.6 | Setup: S2-RAG (AST) descriptive | Tasks: 100 | Passed: 78/100

| Nr | Repo | TaskId | Passed | TestSucceeded | ApplySucceeded | Duration(s) |
|---|------|--------|--------|---------------|----------------|-------------|
| 1 | ansible_refactor | add-log-parameter-get-group-vars | True | True | True | 687.8 |
| 2 | ansible_refactor | add-log-parameter-is-systemd-managed | True | True | True | 780.0 |
| 3 | ansible_refactor | combine-namespace-compat | True | True | True | 320.6 |
| 4 | ansible_refactor | data-to-inventory-data | True | True | True | 173.4 |
| 5 | ansible_refactor | move-quoting-splitter | True | True | True | 589.9 |
| 6 | ansible_refactor | new-inventory-patterns | True | True | True | 301.6 |
| 7 | ansible_refactor | new-utils-class-connection | True | True | True | 1061.9 |
| 8 | ansible_refactor | new-utils-from-basic | False | False | True | 1337.4 |
| 9 | ansible_refactor | parse_key_value | True | True | True | 312.1 |
| 10 | ansible_refactor | rename-lenient-lowercase | True | True | True | 614.7 |
| 11 | ansible_refactor | sort-groups-to-group-sort | True | True | True | 344.4 |
| 12 | celery_refactor | add-log-parameter-get-digest-algorithm | True | True | True | 196.8 |
| 13 | celery_refactor | add-log-parameter-node-format | True | True | True | 1236.7 |
| 14 | celery_refactor | annotation-utils | False | False | True | 1082.9 |
| 15 | celery_refactor | autoretry-to-retry | True | True | True | 872.3 |
| 16 | celery_refactor | combine-unpickle-task | True | True | True | 411.4 |
| 17 | celery_refactor | dump-message-to-serialization | True | True | True | 290.4 |
| 18 | celery_refactor | ensure_serialize | False | False | True | 391.7 |
| 19 | celery_refactor | evaluate-promises-to-serialization | True | True | True | 1558.7 |
| 20 | celery_refactor | expand-router-string-to-utils | True | True | True | 222.8 |
| 21 | celery_refactor | object-mro-lookup | True | True | True | 92.7 |
| 22 | celery_refactor | rename-host-format | True | True | True | 564.8 |
| 23 | celery_refactor | truncate-text | False | False | True | 402.4 |
| 24 | django_refactor | add-log-parameter-constant-time-compare | True | True | True | 838.7 |
| 25 | django_refactor | add-log-parameter-get-resolver | False | False | True | 686.6 |
| 26 | django_refactor | add-log-parameter-resolve-error-handler | True | True | True | 147.7 |
| 27 | django_refactor | add-none-handling-duration-string | True | True | True | 216.3 |
| 28 | django_refactor | combine-utils-dates-dateformat | True | True | True | 315.0 |
| 29 | django_refactor | combine-utils-hashable-itercompat | True | True | True | 718.4 |
| 30 | django_refactor | new-converter-to-python-class | True | True | True | 348.3 |
| 31 | django_refactor | new-path-traversal-exception | False | False | False | 1888.5 |
| 32 | django_refactor | new-reference-context-field-class | True | True | True | 1625.2 |
| 33 | django_refactor | new-reference-context-graph-class | True | True | True | 1357.0 |
| 34 | django_refactor | new-timezone-class | True | True | True | 441.4 |
| 35 | django_refactor | new-utils-adapt-method-mode | True | True | True | 538.2 |
| 36 | django_refactor | new-utils-check-response | True | True | True | 289.3 |
| 37 | django_refactor | new-utils-path-from-module | True | True | True | 198.3 |
| 38 | django_refactor | remove-core-cache-utils | True | True | True | 184.1 |
| 39 | django_refactor | remove-db-models-constants | True | True | True | 1137.8 |
| 40 | django_refactor | rename-file-move-safe | True | True | True | 372.9 |
| 41 | django_refactor | split-parse-apps-and-model-labels | True | True | True | 192.5 |
| 42 | fastapi_refactor | add-log-parameter-generate-option-id-for-path | False | False | True | 400.9 |
| 43 | fastapi_refactor | exception-handlers-to-handlers | False | False | True | 451.0 |
| 44 | fastapi_refactor | get-auth-scheme-param | False | False | True | 602.9 |
| 45 | fastapi_refactor | openapi-get-utils | True | True | True | 528.2 |
| 46 | fastapi_refactor | params-to-param | False | False | True | 773.9 |
| 47 | fastapi_refactor | value-is-a-sequence | False | False | True | 454.0 |
| 48 | flask_refactor | add-log-parameter-get-debug-flag | True | True | True | 193.4 |
| 49 | flask_refactor | add-log-parameter-get-flashed-messages | True | True | True | 623.9 |
| 50 | flask_refactor | debughelpers-to-helpers.py | True | True | False | 27.3 |
| 51 | flask_refactor | rename-send-from-directory | False | False | True | 679.0 |
| 52 | flask_refactor | render-template-str | True | True | True | 858.1 |
| 53 | flask_refactor | stream-template-str | True | True | True | 352.3 |
| 54 | requests_refactor | add-log-parameter-get-encoding-from-headers | True | True | True | 274.2 |
| 55 | requests_refactor | add-log-parameter-resolve-proxies | True | True | True | 374.4 |
| 56 | requests_refactor | add-log-parameter-select-proxy | True | True | True | 208.3 |
| 57 | requests_refactor | combine-from-key-to-key | True | True | False | 1885.0 |
| 58 | requests_refactor | combine-internal-utils-utils | False | False | False | 1659.9 |
| 59 | requests_refactor | move-hooks-sessions | True | True | True | 1150.9 |
| 60 | requests_refactor | new-cookie-utils-class | True | True | True | 1384.9 |
| 61 | requests_refactor | rename-lookup-dict-dict-lookup | True | True | True | 165.7 |
| 62 | requests_refactor | rename-super-len-complex-len | True | True | True | 483.8 |
| 63 | requests_refactor | split-warnings-exceptions | True | True | True | 1853.3 |
| 64 | salt_refactor | add-log-parameter-delete-directory | True | True | True | 420.9 |
| 65 | salt_refactor | add-log-parameter-get-capability-definitions | True | True | True | 402.7 |
| 66 | salt_refactor | add-log-parameter-recursive-diff | True | True | True | 541.3 |
| 67 | salt_refactor | cant-create | False | False | False | 1800.6 |
| 68 | salt_refactor | channel-to-transport | False | False | True | 348.3 |
| 69 | salt_refactor | ex-pillar-fail | True | True | True | 178.6 |
| 70 | salt_refactor | ex-state-fail | False | False | False | 1675.6 |
| 71 | salt_refactor | exactly-n-boto-mod | False | False | False | 1679.7 |
| 72 | salt_refactor | get-unavail | True | True | True | 345.5 |
| 73 | salt_refactor | iam-to-aws | True | True | True | 285.2 |
| 74 | salt_refactor | mksls-to-specific | True | True | True | 661.4 |
| 75 | salt_refactor | namecheap-xmlutil | True | True | True | 1693.5 |
| 76 | salt_refactor | paged-call-boto-mod | True | True | True | 317.0 |
| 77 | salt_refactor | pem-fingerprint | True | True | True | 1055.1 |
| 78 | salt_refactor | perm-denied | True | True | True | 255.0 |
| 79 | scrapy_refactor | add-log-parameter-disconnect-all | True | True | True | 158.7 |
| 80 | scrapy_refactor | add-log-parameter-job-dir | True | True | True | 180.8 |
| 81 | scrapy_refactor | add-log-parameter-xmliter | True | True | True | 551.6 |
| 82 | scrapy_refactor | genspider-functions-to-utils-url | True | True | True | 174.4 |
| 83 | scrapy_refactor | new-downloadermiddlewares-utils | True | True | True | 148.6 |
| 84 | scrapy_refactor | new-spider-utils-in-spiders | True | True | False | 914.0 |
| 85 | scrapy_refactor | new-verify-reactor-class | True | True | True | 1838.1 |
| 86 | scrapy_refactor | not-supported-exception-to-unsupported | True | True | True | 373.2 |
| 87 | scrapy_refactor | parameterize-gunzip | False | False | True | 253.7 |
| 88 | scrapy_refactor | rename-description-commands | True | True | True | 313.6 |
| 89 | scrapy_refactor | rename-engine-status | True | True | True | 137.3 |
| 90 | scrapy_refactor | rename-processtest-testproc | True | True | True | 141.4 |
| 91 | scrapy_refactor | sitemap-url-to-url | True | True | True | 149.2 |
| 92 | tornado_refactor | global-objects | True | True | True | 393.5 |
| 93 | tornado_refactor | log-utils | False | False | True | 782.8 |
| 94 | tornado_refactor | option-parser-with-pretty-print | False | False | True | 767.6 |
| 95 | tornado_refactor | options-utils | True | True | True | 492.1 |
| 96 | tornado_refactor | remove-locale-data | True | True | True | 149.1 |
| 97 | tornado_refactor | rename-http1connection | True | True | True | 266.9 |
| 98 | tornado_refactor | rename-to-camel-case | True | True | True | 236.3 |
| 99 | tornado_refactor | resolvers-as-separate | False | False | True | 1843.2 |
| 100 | tornado_refactor | tcpclient-connect-params | False | False | True | 659.6 |