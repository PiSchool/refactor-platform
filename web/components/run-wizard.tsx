'use client';

import { useMemo, useState } from 'react';
import { X, Search } from 'lucide-react';
import { useBenchmarkTasks, useCatalog, useCreateRun, useModels } from '@/lib/api';
import { Btn, Card } from '@/components/ui';
import type { BenchmarkCat } from '@/lib/types';

const STEPS = ['Benchmark', 'Tasks', 'Coding Tool', 'Setup', 'Timeouts'];
const PAGE = 200;

type Task = { taskKey: string; title: string; params: Record<string, unknown> };

export function RunWizard({ onClose }: { onClose: () => void }) {
  const { data: catalog } = useCatalog();
  const { data: modelCatalog } = useModels();
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
                    <p className="text-xs text-fg-muted">{b.taskCount} tasks · {b.language}</p>
                    {b.dataState !== 'ready' && <p className="mt-1 text-[10px] text-attention-fg">data: {b.dataState}</p>}
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
                        <span className="text-[10px] uppercase tracking-wide text-fg-subtle">{f.label}</span>
                        <select
                          value={facetSel[f.key] ?? ''}
                          onChange={(e) => { setFacetSel((s) => ({ ...s, [f.key]: e.target.value })); setLimit(PAGE); }}
                          className="h-8 min-w-[9rem] rounded-md border border-border bg-canvas-inset px-2 text-xs text-fg">
                          <option value="">All ({allTasks.length})</option>
                          {values.map(([v, n]) => <option key={v} value={v}>{v} ({n})</option>)}
                        </select>
                      </label>
                    );
                  })}
                  <label className="flex min-w-[12rem] flex-1 flex-col gap-1">
                    <span className="text-[10px] uppercase tracking-wide text-fg-subtle">Search</span>
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
                    <label key={t.taskKey} className="flex items-center gap-2 rounded px-2 py-1 text-xs hover:bg-neutral-subtle">
                      <input type="checkbox" checked={taskKeys.includes(t.taskKey)}
                        onChange={(e) => setTaskKeys((k) => e.target.checked ? [...k, t.taskKey] : k.filter((x) => x !== t.taskKey))} />
                      <span className="truncate text-fg">{t.title || t.taskKey}</span>
                      <span className="ml-auto shrink-0 font-mono text-[10px] text-fg-subtle">{t.taskKey.split('/')[0]}</span>
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
                    <button key={a.id} onClick={() => { setAgentId(a.id); if (!model) setModel(a.models[0] || ''); }}
                      className={`rounded-md border p-3 text-left ${agentId === a.id ? 'border-accent-fg bg-accent-subtle/30' : 'border-border hover:border-fg-muted'}`}>
                      <p className="text-sm font-medium text-fg">{a.name}</p>
                      <p className="text-xs text-fg-muted">BYOK · any provider model</p>
                    </button>
                  ))}
                </div>

                {agent && (
                  <div className="space-y-2">
                    <div className="flex items-end gap-2">
                      <label className="flex-1">
                        <span className="text-[10px] uppercase tracking-wide text-fg-subtle">Model</span>
                        <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="provider/model-id"
                          className="mt-1 h-8 w-full rounded-md border border-border bg-canvas-inset px-3 text-sm text-fg" />
                      </label>
                      <label className="flex items-center gap-1 pb-2 text-[11px] text-fg-muted">
                        <input type="checkbox" checked={freeOnly} onChange={(e) => setFreeOnly(e.target.checked)} />
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
                            {m.free && <span className="shrink-0 rounded bg-success-subtle px-1 text-[10px] text-success-fg">free</span>}
                            <span className="ml-auto shrink-0 font-mono text-[10px] text-fg-subtle">{m.id}</span>
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
                  const capOk = !agent || Object.entries(s.capabilities).every(([k, v]) => !v || agent.capabilities[k]);
                  const disabled = !supported || !capOk;
                  return (
                    <label key={s.key} className={`flex items-center gap-2 rounded-md border p-2.5 ${disabled ? 'opacity-40' : 'cursor-pointer hover:border-fg-muted'} ${setupKey === s.key ? 'border-accent-fg' : 'border-border'}`}>
                      <input type="radio" name="setup" disabled={disabled} checked={setupKey === s.key} onChange={() => setSetupKey(s.key)} />
                      <div>
                        <p className="text-sm text-fg">{s.name}</p>
                        <p className="text-xs text-fg-muted">{disabled ? (supported ? 'agent lacks capability' : 'not supported by benchmark') : s.description}</p>
                      </div>
                    </label>
                  );
                })}
              </div>
            )}

            {/* ── Timeouts + summary ────────────────────────────────────── */}
            {step === 4 && (
              <div className="space-y-3">
                <label className="block text-xs text-fg-muted">Per-task timeout (seconds)</label>
                <input type="number" value={timeout} onChange={(e) => setTimeoutS(Number(e.target.value))}
                  className="h-8 w-40 rounded-md border border-border bg-canvas-inset px-3 text-sm text-fg" />
                <div className="rounded-md border border-border p-3 text-xs text-fg-muted">
                  <p>Benchmark: <span className="text-fg">{benchmark?.name}</span></p>
                  <p>Tasks: <span className="text-fg">{taskKeys.length}</span></p>
                  <p>Tool / model: <span className="text-fg">{agent?.name} · {model}</span></p>
                  <p>Setup: <span className="text-fg">{setupKey}</span></p>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between border-t border-border px-4 py-3">
            <Btn variant="invisible" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>Back</Btn>
            {step < 4
              ? <Btn variant="primary" onClick={() => setStep((s) => Math.min(4, s + 1))}>Next</Btn>
              : <Btn variant="primary" loading={create.isPending} disabled={!canLaunch} onClick={launch}>Launch</Btn>}
          </div>
        </div>
      </Card>
    </div>
  );
}
