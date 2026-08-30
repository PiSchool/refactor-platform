// API shapes mirrored from the backend (app/api/serializers.py). camelCase.

import type { Metric } from './metrics';

export type JsonObject = Record<string, unknown>;
export type StepMetrics = JsonObject;
export interface JobStep { kind: string; status: string; detail?: JsonObject }

export interface Counts { total: number; passed: number; failed: number; timedOut: number; pending: number }

export interface RunSummary {
  config?: Record<string, unknown>;
  id: string;
  status: string;
  benchmark: { key: string; name: string; language: string };
  setup: { key: string; name: string };
  agentTool: { key: string; name: string };
  model: string;
  taskTimeoutSeconds: number;
  counts: Counts;
  passRate: number;
  queuedAt: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  tasks?: RunTask[];
}

export interface ArtifactRef {
  key: string;
  available: boolean;
  mediaType: string;
  sizeBytes: number;
  viewUrl: string;
  downloadUrl: string;
}

export interface TaskResult {
  passed: boolean;
  reason: string | null;
  durationSeconds: number;
  agentSeconds: number;
  evaluateSeconds: number;
  tokensInput: number;
  tokensOutput: number;
  model: string;
  metrics: JsonObject;
  details: JsonObject;
}

export interface AgentSessionInfo {
  id: string; role: string; status: string; startedAt: string | null; finishedAt: string | null;
  artifacts: ArtifactRef[];
}

export interface RunTask {
  id: string;
  taskKey: string;
  title: string;
  ordinal: number;
  status: string;
  timeoutSeconds: number;
  startedAt: string | null;
  finishedAt: string | null;
  params: JsonObject;
  /** Known from the task directory, so the prompt is readable mid-run. */
  artifacts: ArtifactRef[];
  result: TaskResult | null;
  session: AgentSessionInfo | null;
}

export interface Facet { key: string; label: string }
export interface BenchmarkCat {
  id: string; key: string; name: string; language: string; taskCount: number;
  dataState: string; facets: Facet[]; setups: string[];
}
export interface AgentCat {
  id: string; key: string; name: string; capabilities: Record<string, boolean>;
  /** The CLI the adapter drives, whether it is on PATH, and how to install it. */
  binary?: string; available?: boolean; install?: string;
}
export interface SetupCat { key: string; name: string; description: string; capabilities: Record<string, boolean> }
export interface Catalog { benchmarks: BenchmarkCat[]; agents: AgentCat[]; setups: SetupCat[] }

export interface Overview { runsTotal: number; runningCount: number; activeRuns: RunSummary[]; recentRuns: RunSummary[] }

export interface BenchmarkPlugin {
  key: string; name: string; language: string;
  taskCount: number; dataState: string; dataError?: string; setups: string[];
}
/** The executable a plugin drives, as this deployment finds it: `bundled` when
 *  the plugin declares no external command. The version is what the command
 *  reports, so it cannot disagree with the one that runs. */
export interface ToolCommand {
  binary: string; state: 'ok' | 'absent' | 'bundled'; version: string; install: string;
}
export interface AgentPlugin {
  key: string; name: string; capabilities: Record<string, boolean>;
  available?: boolean; command: ToolCommand;
}
/** A metric shipped on its own, usable from any benchmark's pipeline. */
/** A metric as the inventory lists it: what the platform describes, plus the
 *  command that installs what it needs when that is missing. */
export interface MetricPlugin extends Metric { install: string }
export interface LspPlugin { key: string; name: string; language: string; available: boolean }

/** A model provider declared in config.yaml. Keys are never sent, only their state. */
export interface ProviderInfo {
  key: string; name: string; baseUrl: string; apiKeyEnv: string;
  keyState: 'present' | 'absent' | 'not-required';
  credits: boolean; active: boolean;
}

export interface SettingsDoc {
  editable: {
    activeModel: string; defaultTaskTimeout: number;
    retentionCap: number; evalToolMaxAttempts: number; keepWorkspace: boolean;
    /** model used for "what would this have cost on X" projections */
    costModel: string;
  };
  secrets: Record<string, string>;
  providers: ProviderInfo[];
  plugins: {
    benchmarks: BenchmarkPlugin[];
    agents: AgentPlugin[];
    metrics: MetricPlugin[];
    lsp: LspPlugin[];
  };
  errors: string[];
}

/** A value the benchmark substitutes into a template. A required one that the
 *  edited template drops is refused on save. */
export interface PromptVariable {
  name: string;
  summary: string;
  required: boolean;
  present: boolean;
}

export interface PromptInfo {
  name: string;
  overridden: boolean;
  /** which tasks select this template; empty when the benchmark says nothing */
  appliesTo: string;
  /** `format` for `{name}` placeholders, `jinja` for `{{ expression }}` */
  syntax: string;
}

export interface PromptDoc {
  name: string;
  overridden: boolean;
  content: string;
  default: string;
  appliesTo: string;
  syntax: string;
  variables: PromptVariable[];
}
