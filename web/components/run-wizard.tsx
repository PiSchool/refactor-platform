'use client';

import { useMemo, useState } from 'react';
import { CircleAlert, Search, TerminalSquare, X } from 'lucide-react';
import { useBenchmarkTasks, useCatalog, useCreateRun, useModels, useSettings } from '@/lib/api';
import { Btn, Card, Select } from '@/components/ui';
import { Checkbox, Chip, Switch } from '@/components/controls';
import type { AgentCat, BenchmarkCat } from '@/lib/types';

const STEPS = ['Benchmark', 'Tasks', 'Coding tool', 'Setup', 'Review'];
const PAGE = 200;

/** One coding tool. An adapter whose CLI is absent from the backend cannot be
 *  chosen: the run would fail inside the terminal and be read as an agent
 *  failure, so the install command is shown instead. */
export function AgentChoice({ agent, selected, onSelect }: {
  agent: AgentCat;
  selected: boolean;
  onSelect: () => void;
}) {
  const missing = agent.available === false;
  return (
    <button disabled={missing} onClick={onSelect}
      title={missing ? `${agent.binary} is not installed on the backend` : undefined}
      className={`rounded-md border p-3 text-left ${missing ? 'cursor-not-allowed border-border opacity-50' : selected ? 'border-accent-fg bg-accent-subtle/30' : 'border-border hover:border-fg-muted'}`}>
      <p className="flex items-center gap-1.5 text-sm font-medium text-fg">
        <TerminalSquare className="h-3.5 w-3.5 shrink-0 text-fg-muted" aria-hidden="true" />
        {agent.name}
      </p>
      {missing
        ? <p className="mt-1 flex items-center gap-1 text-xs text-danger-fg">
            <CircleAlert className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span className="font-mono">{agent.binary}</span> is not installed
            {agent.install ? <Chip mono tone="neutral" title={`Install it with: ${agent.install}`}>{agent.install}</Chip> : null}
          </p>
        : <p className="mt-1 text-xs text-fg-muted">any provider model</p>}
    </button>
  );
}

type Task = { taskKey: string; title: string; params: Record<string, unknown> };

export function LaunchControl({ canLaunch, loading, onLaunch }: {
  canLaunch: boolean;
  loading: boolean;
  onLaunch: () => void;
}) {
  return <Btn variant="primary" loading={loading} disabled={!canLaunch} onClick={onLaunch}>Launch</Btn>;
}

export function RunWizard({ onClose }: { onClose: () => void }) {
  const { data: catalog } = useCatalog();
  const { data: modelCatalog } = useModels();
  const { data: settings } = useSettings();
  const [step, setStep] = useState(0);
  const [benchmark, setBenchmark] = useState<BenchmarkCat | null>(null);
  const [taskKeys, setTaskKeys] = useState<string[]>([]);
  const [agentId, setAgentId] = useState('');
  const [model, setModel] = useState('');
  const [setupKey, setSetupKey] = useState('');
  const [timeout, setTimeoutS] = useState(1800);
  const [search, setSearch] = useState('');
  const [facetSel, setFacetSel] = useState<Record<string, string>>({});
  const [freeOnly, setFreeOnly] = useState(false);
  const [modelQuery, setModelQuery] = useState('');
  const [limit, setLimit] = useState(PAGE);
  const create = useCreateRun();

  const { data: tasksDoc } = useBenchmarkTasks(benchmark?.id ?? null);
  const agent = catalog?.agents.find((a) => a.id === agentId);
  const allTasks: Task[] = tasksDoc?.tasks ?? [];
  const facets = benchmark?.facets ?? [];

  /** Distinct values per declared facet, with counts — from real task params. */
  const facetValues = useMemo(() => {
    const out: Record<string, Map<string, number>> = {};
    for (const f of facets) out[f.key] = new Map();
    for (const t of allTasks) {
      for (const f of facets) {
        const v = t.params?.[f.key];
        if (v == null || v === '') continue;
        const k = String(v);
        out[f.key].set(k, (out[f.key].get(k) ?? 0) + 1);
      }
    }
    return out;
  }, [allTasks, facets]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return allTasks.filter((t) => {
      for (const [key, val] of Object.entries(facetSel)) {
        if (val && String(t.params?.[key] ?? '') !== val) return false;
      }
      if (!q) return true;
      return t.taskKey.toLowerCase().includes(q) || (t.title ?? '').toLowerCase().includes(q);
    });
  }, [allTasks, facetSel, search]);

  const shown = filtered.slice(0, limit);
  const filteredKeys = useMemo(() => filtered.map((t) => t.taskKey), [filtered]);
  const allFilteredSelected = filteredKeys.length > 0 && filteredKeys.every((k) => taskKeys.includes(k));

  const models = useMemo(() => {
    const list = modelCatalog?.models ?? [];
    const q = modelQuery.trim().toLowerCase();
    return list
      .filter((m) => (!freeOnly || m.free) && (!q || m.id.toLowerCase().includes(q) || m.name.toLowerCase().includes(q)))
      .slice(0, 80);
  }, [modelCatalog, modelQuery, freeOnly]);

  const canLaunch = benchmark && taskKeys.length > 0 && agentId && model && setupKey;

  async function launch() {
    if (!canLaunch) return;
    await create.mutateAsync({
      benchmarkId: benchmark!.id, setupId: setupKey, agentToolId: agentId,
      model, taskKeys, taskTimeoutSeconds: timeout,
    });
    onClose();
  }

  function resetFilters() {
    setFacetSel({});
    setSearch('');
    setLimit(PAGE);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <Card className="flex max-h-[88vh] w-full max-w-3xl flex-col">
        <div onClick={(e) => e.stopPropagation()} className="flex flex-col overflow-hidden">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <h2 className="text-sm font-semibold text-fg">New run</h2>
            <button onClick={onClose} className="text-fg-muted hover:text-fg"><X className="h-4 w-4" /></button>
          </div>

          <div className="flex gap-1 border-b border-border px-4 py-2">
            {STEPS.map((s, i) => (
              <button key={s} onClick={() => setStep(i)}
                className={`rounded-full px-2.5 py-1 text-xs ${i === step ? 'bg-accent-subtle text-accent-fg' : 'text-fg-muted hover:bg-neutral-subtle'}`}>
                {i + 1}. {s}
              </button>
            ))}
          </div>

          <div className="min-h-[340px] flex-1 overflow-auto p-4">
            {/* ── Benchmark ─────────────────────────────────────────────── */}
            {step === 0 && (
              <div className="grid gap-2 sm:grid-cols-2">
                {catalog?.benchmarks.map((b) => (
                  <button key={b.id} disabled={b.dataState !== 'ready'}
                    onClick={() => { setBenchmark(b); setTaskKeys([]); setSetupKey(''); resetFilters(); setStep(1); }}
                    className={`rounded-md border p-3 text-left disabled:opacity-40 ${benchmark?.id === b.id ? 'border-accent-fg bg-accent-subtle/30' : 'border-border hover:border-fg-muted'}`}>
                    <p className="text-sm font-medium text-fg">{b.name}</p>
                    <p className="text-xs text-fg-muted">{b.taskCount.toLocaleString()} tasks · {b.language}</p>
                    {b.dataState !== 'ready' && <p className="mt-1 text-[11px] text-attention-fg">data: {b.dataState}</p>}
                  </button>
                ))}
              </div>
            )}

            {/* ── Tasks: faceted filtering ──────────────────────────────── */}
            {step === 1 && benchmark && (
              <div className="space-y-3">
                <div className="flex flex-wrap items-end gap-2">
                  {facets.map((f) => {
                    const values = [...(facetValues[f.key]?.entries() ?? [])].sort((a, b) => b[1] - a[1]);
                    if (!values.length) return null;
                    return (
                      <label key={f.key} className="flex flex-col gap-1">
                        <span className="text-[11px] uppercase tracking-wide text-fg-subtle">{f.label}</span>
                        <Select
                          value={facetSel[f.key] ?? ''}
                          className="min-w-[9rem]"
                          onChange={(e) => { setFacetSel((s) => ({ ...s, [f.key]: e.target.value })); setLimit(PAGE); }}>
                          <option value="">All · {allTasks.length}</option>
                          {values.map(([v, n]) => <option key={v} value={v}>{v} · {n}</option>)}
                        </Select>
                      </label>
                    );
                  })}
                  <label className="flex min-w-[12rem] flex-1 flex-col gap-1">
                    <span className="text-[11px] uppercase tracking-wide text-fg-subtle">Search</span>
                    <div className="relative">
                      <Search className="pointer-events-none absolute left-2 top-2 h-3.5 w-3.5 text-fg-subtle" />
                      <input value={search} onChange={(e) => { setSearch(e.target.value); setLimit(PAGE); }}
                        placeholder="task key or title…"
                        className="h-8 w-full rounded-md border border-border bg-canvas-inset pl-7 pr-2 text-xs text-fg" />
                    </div>
                  </label>
                  <Btn variant="invisible" onClick={resetFilters}>Reset</Btn>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <Btn variant="outline"
                    onClick={() => setTaskKeys((k) => allFilteredSelected
                      ? k.filter((x) => !filteredKeys.includes(x))
                      : Array.from(new Set([...k, ...filteredKeys])))}>
                    {allFilteredSelected ? 'Deselect' : 'Select'} all {filtered.length} matching
                  </Btn>
                  <Btn variant="invisible" onClick={() => setTaskKeys([])}>Clear</Btn>
                  <span className="ml-auto text-fg-muted">{taskKeys.length} selected · {filtered.length} match</span>
                </div>

                <div className="max-h-72 space-y-0.5 overflow-auto rounded-md border border-border p-1">
                  {shown.map((t) => (
                    <label key={t.taskKey} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-xs hover:bg-neutral-subtle">
                      <Checkbox checked={taskKeys.includes(t.taskKey)} label={t.taskKey}
                        onChange={(on) => setTaskKeys((k) => (on ? [...k, t.taskKey] : k.filter((x) => x !== t.taskKey)))} />
                      <span className="truncate text-fg" title={t.taskKey}>{t.title || t.taskKey}</span>
                      <span className="ml-auto shrink-0 font-mono text-[11px] text-fg-subtle">{t.taskKey.split('/')[0]}</span>
                    </label>
                  ))}
                  {filtered.length === 0 && <p className="p-3 text-xs text-fg-subtle">No tasks match these filters.</p>}
                  {filtered.length > shown.length && (
                    <button onClick={() => setLimit((l) => l + PAGE)}
                      className="w-full rounded py-1.5 text-xs text-accent-fg hover:bg-neutral-subtle">
                      Show {Math.min(PAGE, filtered.length - shown.length)} more ({filtered.length - shown.length} hidden)
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* ── Coding tool + model ───────────────────────────────────── */}
            {step === 2 && (
              <div className="space-y-3">
                <div className="grid gap-2 sm:grid-cols-2">
                  {catalog?.agents.map((a) => (
                    <AgentChoice key={a.id} agent={a} selected={agentId === a.id}
                      onSelect={() => {
                        setAgentId(a.id);
                        // The deployment's configured default, not a per-tool list:
                        // every tool reaches the same provider and accepts any
                        // model id it serves.
                        if (!model) setModel(settings?.editable.activeModel || '');
                      }} />
                  ))}
                </div>

                {agent && (
                  <div className="space-y-2">
                    <div className="flex items-end gap-2">
                      <label className="flex-1">
                        <span className="text-[11px] uppercase tracking-wide text-fg-subtle">Model</span>
                        <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="provider/model-id"
                          className="mt-1 h-8 w-full rounded-md border border-border bg-canvas-inset px-3 text-sm text-fg" />
                      </label>
                      <label className="flex items-center gap-1.5 pb-2 text-xs text-fg-muted">
                        <Switch checked={freeOnly} onChange={setFreeOnly}
                          label="Show only models the provider charges nothing for" />
                        free only
                      </label>
                    </div>

                    <input value={modelQuery} onChange={(e) => setModelQuery(e.target.value)} placeholder="Search models…"
                      className="h-8 w-full rounded-md border border-border bg-canvas-inset px-3 text-xs text-fg" />

                    {modelCatalog && (modelCatalog.source === 'provider' || modelCatalog.source === 'cache') ? (
                      <div className="max-h-48 overflow-auto rounded-md border border-border">
                        {models.map((m) => (
                          <button key={m.id} onClick={() => setModel(m.id)}
                            className={`flex w-full items-center gap-2 px-2 py-1 text-left text-xs hover:bg-neutral-subtle ${model === m.id ? 'bg-accent-subtle/40' : ''}`}>
                            <span className="truncate text-fg">{m.name}</span>
                            {m.free && <Chip tone="success" title="The provider charges nothing for this model">free</Chip>}
                            <span className="ml-auto shrink-0 font-mono text-[11px] text-fg-subtle">{m.id}</span>
                          </button>
                        ))}
                        {models.length === 0 && <p className="p-2 text-xs text-fg-subtle">No models match.</p>}
                      </div>
                    ) : (
                      <p className="rounded-md border border-border p-2 text-xs text-fg-subtle">
                        Model catalog unavailable ({modelCatalog?.source ?? 'loading'}). Type any model id above.
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ── Setup ─────────────────────────────────────────────────── */}
            {step === 3 && benchmark && (
              <div className="space-y-2">
                {catalog?.setups.map((s) => {
                  const supported = benchmark.setups.includes(s.key);
                  // Which capability the chosen tool is missing, by name: "agent
                  // lacks capability" gave an operator nothing to act on.
                  const lacking = agent
                    ? Object.entries(s.capabilities).filter(([key, needed]) => needed && !agent.capabilities[key]).map(([key]) => key)
                    : [];
                  const disabled = !supported || lacking.length > 0;
                  const why = !supported
                    ? `${benchmark.name} does not offer this setup`
                    : lacking.length > 0
                      ? `${agent?.name} provides no ${lacking.join(', ')}`
                      : '';
                  return (
                    <label key={s.key} title={why || s.description}
                      className={`flex items-start gap-2 rounded-md border p-2.5 ${disabled ? 'opacity-50' : 'cursor-pointer hover:border-fg-muted'} ${setupKey === s.key ? 'border-accent-fg bg-accent-subtle/20' : 'border-border'}`}>
                      <input type="radio" name="setup" disabled={disabled} checked={setupKey === s.key}
                        onChange={() => setSetupKey(s.key)}
                        className="mt-0.5 h-3.5 w-3.5 shrink-0 accent-accent-fg" />
                      <div className="min-w-0">
                        <p className="flex items-center gap-1.5 text-sm text-fg">
                          {s.name}
                          <code className="font-mono text-[11px] text-fg-subtle">{s.key}</code>
                        </p>
                        {why
                          ? <p className="mt-0.5 flex items-center gap-1 text-xs text-attention-fg">
                              <CircleAlert className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />{why}
                            </p>
                          : <p className="mt-0.5 text-xs text-fg-muted">{s.description}</p>}
                      </div>
                    </label>
                  );
                })}
              </div>
            )}

            {/* ── Timeout + summary ─────────────────────────────────────── */}
            {step === 4 && (
              <div className="space-y-3">
                <label className="flex flex-col gap-1" htmlFor="task-timeout">
                  <span className="text-[11px] uppercase tracking-wide text-fg-subtle">Task timeout</span>
                  <span className="relative inline-flex w-40 items-center">
                    <input id="task-timeout" type="number" value={timeout} onChange={(e) => setTimeoutS(Number(e.target.value))}
                      className="h-8 w-40 rounded-md border border-border bg-canvas-inset pl-3 pr-7 text-sm text-fg outline-none focus:border-accent-fg" />
                    <span className="pointer-events-none absolute right-2 text-[11px] text-fg-subtle">s</span>
                  </span>
                </label>
                <dl className="grid grid-cols-[7rem_1fr] gap-x-3 gap-y-1 rounded-md border border-border p-3 text-xs">
                  <dt className="text-fg-subtle">Benchmark</dt>
                  <dd className="truncate text-fg">{benchmark?.name}</dd>
                  <dt className="text-fg-subtle">Tasks</dt>
                  <dd className="tabular-nums text-fg">{taskKeys.length}</dd>
                  <dt className="text-fg-subtle">Coding tool</dt>
                  <dd className="truncate text-fg">{agent?.name}</dd>
                  <dt className="text-fg-subtle">Model</dt>
                  <dd className="truncate font-mono text-fg">{model}</dd>
                  <dt className="text-fg-subtle">Setup</dt>
                  <dd className="truncate text-fg">
                    {catalog?.setups.find((s) => s.key === setupKey)?.name ?? setupKey}
                  </dd>
                </dl>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between border-t border-border px-4 py-3">
            <Btn variant="invisible" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>Back</Btn>
            {step < 4
              ? <Btn variant="primary" onClick={() => setStep((s) => Math.min(4, s + 1))}>Next</Btn>
              : <LaunchControl canLaunch={Boolean(canLaunch)} loading={create.isPending} onLaunch={launch} />}
          </div>
        </div>
      </Card>
    </div>
  );
}
