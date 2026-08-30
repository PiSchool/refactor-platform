/**
 * A metric as the platform describes it, and the rules for editing its options.
 *
 * Every metric is one add-on directory whose name is its id, so there is no
 * distinction here between a shipped metric and someone else's: each declares
 * what it measures, what it needs, whether it can decide a verdict, what it
 * records, and the options it accepts with their types and defaults. Editing is
 * by option, not by hand-written JSON, and an option left empty is removed from
 * the override so the metric's own default applies again.
 */

export type MetricOptionType =
  | 'string'
  | 'integer'
  | 'number'
  | 'boolean'
  | 'choice'
  | 'list'
  | 'reference';

export interface MetricOption {
  key: string;
  label: string;
  type: MetricOptionType;
  default: unknown;
  help: string;
  unit: string;
  choices: string[];
}

export interface Metric {
  /** The metric's id, which is the name of the directory that provides it. */
  id: string;
  title: string;
  summary: string;
  /** What must be present for it to run, in one phrase. */
  requires: string;
  /** False for a metric that only records numbers and can never fail a task. */
  gates: boolean;
  /** Failure code this metric reports. */
  reason: string;
  mutatesWorkspace: boolean;
  outputs: string[];
  options: MetricOption[];
  /** Whether this deployment can run it, and why not. */
  available: boolean;
  unavailable: string;
}

export type StageConfig = Record<string, unknown>;

/** A stage in the benchmark's verify pipeline: which metric runs, how it is
 *  configured, and whether the operator left it on. */
export interface Stage {
  preset: string;
  config: StageConfig;
  enabled: boolean;
  metric: Metric;
}

/** What `GET /api/benchmarks/{key}/evaluation` returns. */
export interface EvaluationDoc {
  benchmark: string;
  overridden: boolean;
  /** The benchmark's own step before anything measures, when it has one. */
  prepare: Metric | null;
  /** Measured on every task and stored; never gates. */
  capture: Metric[];
  shipped: { verify: { preset: string; config: StageConfig }[]; passed: string };
  effective: { verify: Stage[]; passed: string };
  available: Metric[];
}

export interface OptionRow {
  option: MetricOption;
  value: unknown;
  /** False for a configured key the metric does not declare. */
  declared: boolean;
}

/** One line stating what the metric needs, and whether it is here. */
export function requirementLabel(metric: Metric): string {
  if (!metric.available) return metric.unavailable || `${metric.id} is not installed`;
  return metric.requires ? `Needs ${metric.requires}` : '';
}

function inferType(value: unknown): MetricOptionType {
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  if (Array.isArray(value)) return 'list';
  return 'string';
}

/**
 * Declared options first, then anything the manifest configured that the metric
 * does not declare — an undeclared key is still editable rather than invisible.
 */
export function optionRows(metric: Metric, config: StageConfig | undefined): OptionRow[] {
  const set = config ?? {};
  const rows: OptionRow[] = (metric.options ?? []).map((option) => ({
    option,
    value: set[option.key],
    declared: true,
  }));
  const known = new Set((metric.options ?? []).map((o) => o.key));
  for (const [key, value] of Object.entries(set)) {
    if (known.has(key)) continue;
    rows.push({
      declared: false,
      value,
      option: { key, label: key, type: inferType(value), default: null, help: '', unit: '', choices: [] },
    });
  }
  return rows;
}

/** How a value is shown in a text field. */
export function displayValue(value: unknown): string {
  if (value === undefined || value === null) return '';
  if (Array.isArray(value)) return value.map((v) => String(v)).join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/** What is stored for a typed field, or undefined when the field is empty. */
export function coerce(type: MetricOptionType, raw: string): unknown {
  const text = raw.trim();
  if (type === 'list') {
    const items = raw.split(/[,\n]/).map((v) => v.trim()).filter(Boolean);
    return items.length ? items : undefined;
  }
  if (text === '') return undefined;
  if (type === 'integer') {
    const n = Number.parseInt(text, 10);
    return Number.isFinite(n) ? n : undefined;
  }
  if (type === 'number') {
    const n = Number(text);
    return Number.isFinite(n) ? n : undefined;
  }
  if (type === 'boolean') return text === 'true';
  return raw;
}

/** An emptied option is removed, so the metric's declared default applies again. */
export function withOption(config: StageConfig | undefined, key: string, value: unknown): StageConfig {
  const next = { ...(config ?? {}) };
  if (value === undefined) delete next[key];
  else next[key] = value;
  return next;
}

// ─── The verdict expression ──────────────────────────────────────────────────

/**
 * The names the expression may use: every enabled stage, by its full preset and
 * by its last segment, which is how a namespaced stage is normally written.
 * Mirrors the environment the server evaluates against.
 */
export function verdictNames(stages: Stage[]): string[] {
  const names: string[] = [];
  for (const stage of stages) {
    if (stage.enabled && !names.includes(stage.preset)) names.push(stage.preset);
  }
  return names;
}

/** The rule an empty expression stands for: every enabled stage must pass. */
export function defaultExpression(stages: Stage[]): string {
  return stages.filter((stage) => stage.enabled).map((stage) => stage.preset).join(' and ');
}

type Token = { kind: 'name' | 'op' | 'not' | '(' | ')'; text: string };

const NAME = /^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*/;

function tokenize(expression: string): { tokens: Token[] } | { error: string } {
  const tokens: Token[] = [];
  let at = 0;
  while (at < expression.length) {
    const char = expression[at];
    if (/\s/.test(char)) { at += 1; continue; }
    if (char === '(' || char === ')') { tokens.push({ kind: char, text: char }); at += 1; continue; }
    const match = NAME.exec(expression.slice(at));
    if (!match) return { error: `unexpected character "${char}"` };
    const text = match[0];
    at += text.length;
    if (text === 'and' || text === 'or') tokens.push({ kind: 'op', text });
    else if (text === 'not') tokens.push({ kind: 'not', text });
    else tokens.push({ kind: 'name', text });
  }
  return { tokens };
}

/**
 * Why this expression would be rejected, or an empty string when it holds.
 *
 * The server refuses an invalid expression on save; checking the same grammar
 * here — stage names, `and`, `or`, `not`, parentheses — reports the reason while
 * it is being typed instead of after a failed request.
 */
export function verdictProblem(expression: string, names: string[]): string {
  if (!expression.trim()) return '';
  const scan = tokenize(expression);
  if ('error' in scan) return scan.error;
  const { tokens } = scan;
  const known = new Set(names);
  let at = 0;
  let problem = '';
  const fail = (message: string) => { if (!problem) problem = message; };

  const atom = (): void => {
    const token = tokens[at];
    if (!token) { fail('expected a stage name'); return; }
    if (token.kind === 'not') { at += 1; atom(); return; }
    if (token.kind === '(') {
      at += 1;
      group();
      if (tokens[at]?.kind !== ')') { fail('unclosed "("'); return; }
      at += 1;
      return;
    }
    if (token.kind === 'name') {
      at += 1;
      if (token.text === 'True' || token.text === 'False') return;
      if (!known.has(token.text)) fail(`unknown stage "${token.text}"`);
      return;
    }
    fail('expected a stage name');
    at += 1;
  };

  const group = (): void => {
    atom();
    while (tokens[at]?.kind === 'op') { at += 1; atom(); }
  };

  group();
  if (!problem && at < tokens.length) {
    fail(tokens[at].kind === ')' ? 'unmatched ")"' : `unexpected "${tokens[at].text}"`);
  }
  return problem;
}

// ─── Unsaved edits ───────────────────────────────────────────────────────────

/** Key order must not decide whether two configurations differ. */
function stable(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value) ?? 'null';
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  const entries = Object.entries(value as Record<string, unknown>).sort(([a], [b]) => (a < b ? -1 : 1));
  return `{${entries.map(([key, item]) => `${JSON.stringify(key)}:${stable(item)}`).join(',')}}`;
}

/** Whether the edited pipeline still matches the one the server returned. */
export function pipelineChanged(doc: EvaluationDoc, stages: Stage[], passed: string): boolean {
  if (passed.trim() !== doc.effective.passed.trim()) return true;
  const before = doc.effective.verify;
  if (before.length !== stages.length) return true;
  return stages.some((stage, index) => stage.preset !== before[index].preset
    || stage.enabled !== before[index].enabled
    || stable(stage.config ?? {}) !== stable(before[index].config ?? {}));
}
