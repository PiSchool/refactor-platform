# Configuration

Refactor Platform separates secrets, committed defaults, and operator-editable
runtime values. This keeps deployments reproducible without storing credentials
in Git or the database.

## Configuration layers

| Layer | Location | Intended contents |
|---|---|---|
| Secrets and deployment wiring | `.env` / process environment | Provider keys, database URL, bind addresses, data paths |
| Committed defaults | `config.yaml` | Non-secret server and run defaults |
| Runtime overrides | `runtime_setting` table | Values edited from Settings, such as active model and retention |

Secrets are read directly from the process environment. The API reports only
`present` or `absent`; it never returns the values.

## Provider credentials

Copy the template and edit the ignored file:

```bash
cp .env.example .env
chmod 600 .env
```

### Providers

Providers are declared in `config.yaml`; the environment carries only their
keys. The platform resolves the active provider's endpoint and key and passes
the agent a vendor-neutral `RP_PROVIDER`, `RP_PROVIDER_BASE_URL` and
`RP_PROVIDER_API_KEY`, so adding a provider needs no code change.

| Variable | Required | Default | Description |
|---|---:|---|---|
| `RP_PROVIDER` | no | `defaults.provider` in `config.yaml` | Which declared provider serves runs |
| `OPENROUTER_API_KEY` | for `openrouter` | none | Key for the default provider |
| `OPENROUTER_BASE_URL` | no | `https://openrouter.ai/api/v1` | Endpoint override |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | for `openai` | none / `https://api.openai.com/v1` | Key and endpoint override |
| `LOCAL_LLM_BASE_URL` / `LOCAL_LLM_API_KEY` | for `local` | `http://127.0.0.1:11434/v1` / none | A self-hosted OpenAI-compatible endpoint |

A provider declared with its own `api_key_env` follows the same pattern, and its
key is added to evidence redaction automatically. See
[Extending](extending.md#model-providers).

The Copilot adapter authenticates only through the selected provider: it clears
any GitHub token from the child environment and passes the run's model with
`--model`. A GitHub subscription is not an authentication fallback. The
dashboard catalogue lists the provider's models that advertise text output and
tool support, and the wizard also accepts a model id typed by hand.

## Deployment variables

| Variable | Default | Description |
|---|---|---|
| `RP_WEB_BIND` | `127.0.0.1` | Host interface the dashboard is published on |
| `RP_WEB_PORT` | `3000` | Host port the dashboard is published on |
| `RP_API_BIND` | `127.0.0.1` | Host interface used for the backend's port mapping |
| `RP_DATA_DIR` | `/data` in Compose | Database, outputs, mirrors, and prompt overrides |
| `RP_PLUGINS_DIR` | `/app/plugins` in the backend image | Plugin discovery root |
| `RP_BUILD_REV` | empty | Revision recorded in both images at build time and reported with the running build; a build without it is identified by its source fingerprint alone |
| `DATABASE_URL` | SQLite under `RP_DATA_DIR` | Optional SQLAlchemy URL, including PostgreSQL with `asyncpg` |
| `RETRIEVAL_DB_PASSWORD` | required | Password for the internal pgvector writer; Compose refuses to render when absent |
| `RETRIEVAL_DB_READER_PASSWORD` | required | Distinct password for the SELECT-only MCP role; Compose refuses to render when absent |
| `RETRIEVAL_DATABASE_URL` | composed internally | Synchronous PostgreSQL URL used only by S2; normally supplied by Compose |
| `RETRIEVAL_READER_DATABASE_URL` | composed internally | SELECT-only URL supplied to the per-session MCP server |
| `OLLAMA_HOST` | `http://ollama:11434` | Where the embedding and query-rewriting models are served. The models themselves are set in the `retrieval` section of `config.yaml` |
| `RETRIEVAL_EMBEDDER` | empty | `module:function` returning an embedder, for a deployment that produces embeddings outside the model server. See [Retrieval (S2)](retrieval.md#models) |
| `RETRIEVAL_MODEL_CACHE_DIR` | `$RP_DATA_DIR/models/fastembed` | Persistent model cache |

For PostgreSQL, use an async SQLAlchemy URL:

```dotenv
DATABASE_URL=postgresql+asyncpg://refactor_platform:REDACTED@db.example/refactor_platform
```

Do not put a real password in a tracked example or issue.

## Committed defaults

`config.yaml` contains safe defaults:

```yaml
server:
  host: 0.0.0.0
  port: 8000

defaults:
  provider: openrouter
  model: openrouter/free
  task_timeout_seconds: 1800
  eval_tool_max_attempts: 3
  retention_runs_cap: 25

providers:
  - key: openrouter
    name: OpenRouter
    base_url: https://openrouter.ai/api/v1
    api_key_env: OPENROUTER_API_KEY
    base_url_env: OPENROUTER_BASE_URL
    credits: true

retrieval:
  embedding_model: hf.co/nomic-ai/nomic-embed-code-GGUF:Q4_K_M
  embedding_dimension: 3584
  expansion_model: qwen2.5-coder:7b-instruct
  reranker_model: Xenova/ms-marco-MiniLM-L-6-v2
```

`defaults.model` is the value the wizard starts from, not a restriction: the
published campaign used a free router because it cost nothing.

Changing this file changes defaults for new installations. Existing runtime
overrides continue to take precedence.

## Runtime settings

The Settings page persists these values without rebuilding containers:

| Setting | Effect |
|---|---|
| Default model | Model the run wizard starts from |
| Cost-projection model | Model used for “what would this have cost?” projections |
| Task timeout | Wall-clock limit applied to newly created run tasks |
| Runs kept on disk | Number of recent executed-run artifact trees retained automatically; imported archives are exempt |
| Self-check attempts | Maximum evaluation-tool invocations exposed to `s1_eval` |
| Keep task workspaces | Keeps completed workspaces available to the repository browser |

Plugin manifests remain the source of truth for plugin capabilities. Settings
may tune supported evaluation stages and prompt overrides, but cannot turn an
unavailable plugin or tool into an installed one.

## Evaluation stages

**Settings → Evaluation & metrics** shows the rule that decides a verdict and
every stage that feeds it. The rule is either “every stage passes”, whose
equivalent expression is shown, or an expression over stage names combined with
`and`, `or`, `not` and parentheses. An expression naming a stage that is absent
or switched off is reported as invalid before it can be saved, in the same terms
the server would refuse it.

Each stage arrives with what it measures, what it records, where it comes from —
the platform, a metric plugin, or the benchmark itself — and its options as typed
fields behind a fold. A switch decides whether it runs; a field shows the
metric's own default until a value is entered, and one control restores that
default. A stage that declares nothing is still listed and still configurable, by
its preset name.

Stages under **Recorded** are measured on every task and never decide a verdict.
A metric this deployment ships that the benchmark's manifest does not reference
is listed separately; adding one is a manifest edit
([Adding a benchmark](adding-a-benchmark.md)).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/ui-evaluation-dark.png">
  <img alt="Settings, Evaluation and metrics: the verdict rule over three gating stages, each with its failure reason, what it records, which plugin provides it and how many options it accepts, above the metrics recorded on every task" src="figures/ui-evaluation-light.png">
</picture>

## Prompt templates

**Settings → Prompts** lists each template with the tasks that select it. A
benchmark declares the values it substitutes — in `prompt.variables` in its
manifest, or per template from Python when it builds the prompt itself. The
editor marks each one present or missing and inserts a missing one at the cursor,
and a save that drops a required value is refused rather than producing a prompt
with the task missing from it. Templates use one of two syntaxes and they are not
interchangeable: `{name}` placeholders where the plugin substitutes values
itself, `{{ expression }}` where the platform renders the manifest's template
with Jinja.

## Installed tools

**Settings → Services** reports the deployment itself: what each container was
built from, the credentials and providers it holds, the build and language
toolchain probed inside the backend container with what each is needed for, and
the retrieval pipeline stage by stage with the models and candidate counts each
stage uses. Probe results are cached for five minutes and re-probed on request.

Commands that belong to a plugin — the agent CLIs, the language servers — are
reported under **Settings → Plugins**, beside the plugin that declares them,
with the version the command itself answers with and the install command when it
is absent. Each tool appears in one place.

The deployment group reports a fingerprint of the source each image was built
from — the server package, the plugins and `config.yaml` for the backend, the
dashboard source for the frontend — plus the build time and `RP_BUILD_REV` when
one was recorded. `GET /api/health` carries the backend's under `build`, and
`scripts/deployment_status.py` compares both against the working tree. See
[Confirm what is deployed](deployment.md#confirm-what-is-deployed).

## S2 retrieval configuration

Compose provisions `retrieval-db` from a digest-pinned
`pgvector/pgvector:pg16` image and does not publish its port. Keep both URLs on
the internal network. The backend writer URL
is never passed to the agent. The per-session MCP file receives only the
`retrieval_reader` URL, whose role has SELECT-only/default privileges, and that
private config is excluded from run exports.

Embedding and query expansion run on the `ollama` service, which is part of the
default stack and uses whatever hardware the host gives it. Changing a model or
its dimension creates a new immutable index identity rather than reusing
incompatible vectors.

Search fan-out can be tuned with environment variables:

| Variable | Default | Effect |
|---|---:|---|
| `RETRIEVAL_PREFILTER_CANDIDATES` | `512` | maximum task-scoped chunks embedded after full-corpus BM25/target selection |
| `RETRIEVAL_VECTOR_CANDIDATES` | `50` | cosine candidates per planned query |
| `RETRIEVAL_LEXICAL_CANDIDATES` | `50` | BM25 candidates per planned query |
| `RETRIEVAL_FUSED_CANDIDATES` | `40` | candidates sent to the cross-encoder |
| `RETRIEVAL_CONTEXT_HITS` | `12` | maximum snippets injected |
| `RETRIEVAL_CONTEXT_CHAR_LIMIT` | `24000` | maximum injected context characters |
| `RETRIEVAL_WINDOW_LINES` | `80` | naive chunk size |
| `RETRIEVAL_OVERLAP_LINES` | `20` | naive chunk overlap |

See [Retrieval (S2)](retrieval.md) before changing these values; record
all changes in experiment provenance.

## Credential inventory

Track credential **metadata**, not secret values, in the team's task tracker:

- credential name and purpose;
- owning person or team;
- storage location (for example AWS Secrets Manager, a password manager, or a
  protected host environment file);
- environments where it is used;
- creation and last-rotation dates;
- expiry date and revocation procedure.

Do not paste AWS keys, provider keys, GitHub tokens, private keys, or `.env`
contents into the tracker, GitHub, chat, screenshots, or run exports. Use a
dedicated secret manager for the value and store only its reference in the
inventory.

## Rotation checklist

1. Create the replacement credential in the provider.
2. Update the deployment's protected environment or secret manager.
3. Recreate only the affected service: `docker compose up -d --force-recreate backend`.
4. Verify `GET http://127.0.0.1:8000/api/health` and run a small smoke task.
5. Revoke the old credential.
6. Update ownership and rotation metadata in the credential inventory.

Rotating a retrieval password also requires recreating `retrieval-db`: the role's
password is set from the environment when the database starts.