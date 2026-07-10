// API shapes mirrored from the backend (app/api/serializers.py). camelCase.

export type JsonObject = Record<string, unknown>;
export type StepMetrics = JsonObject;
export interface JobStep { kind: string; status: string; detail?: JsonObject }

export interface Counts { total: number; passed: number; failed: number; timedOut: number; pending: number }

export interface RunSummary {
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
  artifacts: Record<string, string | null>;
}

export interface AgentSessionInfo {
  id: string; role: string; status: string; startedAt: string | null; finishedAt: string | null;
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
  artifacts: Record<string, string>;
  result: TaskResult | null;
  session: AgentSessionInfo | null;
}

export interface Facet { key: string; label: string }
export interface BenchmarkCat {
  id: string; key: string; name: string; language: string; taskCount: number;
  dataState: string; facets: Facet[]; setups: string[];
}
export interface AgentCat { id: string; key: string; name: string; models: string[]; capabilities: Record<string, boolean> }
export interface SetupCat { key: string; name: string; description: string; capabilities: Record<string, boolean> }
export interface Catalog { benchmarks: BenchmarkCat[]; agents: AgentCat[]; setups: SetupCat[] }

export interface Overview { runsTotal: number; runningCount: number; activeRuns: RunSummary[]; recentRuns: RunSummary[] }

export interface BenchmarkPlugin {
  key: string; name: string; language: string; version: string;
  taskCount: number; dataState: string; setups: string[];
}
export interface AgentPlugin { key: string; name: string; version: string; capabilities: Record<string, boolean> }
export interface LspPlugin { key: string; language: string; available: boolean }

export interface SettingsDoc {
  editable: {
    activeModel: string; defaultTaskTimeout: number;
    retentionCap: number; evalToolMaxAttempts: number; keepWorkspace: boolean;
    /** model used for "what would this have cost on X" projections */
    costModel: string;
  };
  secrets: Record<string, string>;
  plugins: {
    benchmarks: BenchmarkPlugin[];
    agents: AgentPlugin[];
    setups: SetupCat[];
    lsp: LspPlugin[];
  };
  errors: string[];
}

export interface PromptInfo { name: string; overridden: boolean }
export interface PromptDoc { name: string; overridden: boolean; content: string; default: string }
