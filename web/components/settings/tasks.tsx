'use client';

/**
 * Which of a benchmark's tasks may be run.
 *
 * The row's trailing label used to read `params.refactoringType ?? params.mode` —
 * two field names from two particular benchmarks, hardcoded into the dashboard,
 * so a third benchmark's tasks showed nothing. A benchmark declares the fields
 * worth grouping by as facets, and both the filters and the row labels come from
 * that declaration.
 */

import { useEffect, useMemo, useState } from 'react';
import { Ban, Check, Search } from 'lucide-react';
import { Btn, Select } from '@/components/ui';
import { Chip, Switch } from '@/components/controls';
import { useCatalog } from '@/lib/api';
import type { Facet } from '@/lib/types';
import { getJson, Note, Panel } from './kit';

interface TaskRow { taskKey: string; title: string; params: Record<string, any>; disabled: boolean }
const PAGE = 100;

/** The declared facet values this task has, in declaration order. */
function facetChips(task: TaskRow, facets: Facet[]): { key: string; label: string; value: string }[] {
  return facets
    .map((facet) => ({ key: facet.key, label: facet.label, value: String(task.params?.[facet.key] ?? '') }))
    .filter((entry) => entry.value !== '');
}

export function TasksSection({ benchmark }: { benchmark: string }) {
  const { data: catalog } = useCatalog();
  const bench = catalog?.benchmarks.find((b) => b.key === benchmark);
  const [rows, setRows] = useState<TaskRow[] | null>(null);
  const [search, setSearch] = useState('');
  const [facetSel, setFacetSel] = useState<Record<string, string>>({});
  const [limit, setLimit] = useState(PAGE);
  const [busy, setBusy] = useState(false);

  const load = () => {
    if (!bench) return;
    getJson<{ tasks: TaskRow[] }>(`/api/benchmarks/${bench.id}/tasks?includeDisabled=true`)
      .then((d) => setRows(d?.tasks ?? []));
  };

  useEffect(() => {
    let stale = false;
    setRows(null); setSearch(''); setFacetSel({}); setLimit(PAGE);
    if (!bench) return;
    getJson<{ tasks: TaskRow[] }>(`/api/benchmarks/${bench.id}/tasks?includeDisabled=true`)
      .then((d) => { if (!stale) setRows(d?.tasks ?? []); });
    return () => { stale = true; };
  }, [bench?.id]);

  const facets = bench?.facets ?? [];
  const facetValues = useMemo(() => {
    const out: Record<string, Map<string, number>> = {};
    for (const f of facets) out[f.key] = new Map();
    for (const t of rows ?? []) {
      for (const f of facets) {
        const v = t.params?.[f.key];
        if (v == null || v === '') continue;
        out[f.key].set(String(v), (out[f.key].get(String(v)) ?? 0) + 1);
      }
    }
    return out;
  }, [rows, facets]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (rows ?? []).filter((t) => {
      for (const [k, v] of Object.entries(facetSel)) if (v && String(t.params?.[k] ?? '') !== v) return false;
      return !q || t.taskKey.toLowerCase().includes(q) || (t.title ?? '').toLowerCase().includes(q);
    });
  }, [rows, facetSel, search]);

  async function toggle(keys: string[], disabled: boolean) {
    setBusy(true);
    await fetch(`/api/benchmarks/${benchmark}/tasks/disable`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ taskKeys: keys, disabled }),
    });
    setBusy(false);
    load();
  }

  const disabledCount = (rows ?? []).filter((t) => t.disabled).length;

  return (
    <Panel title="Tasks" description="A disabled task is hidden from the run wizard and refused at run creation.">
      {!rows ? <Note>Loading…</Note> : (
        <>
          <div className="mb-2 flex flex-wrap items-end gap-2">
            {facets.map((f) => {
              const values = [...(facetValues[f.key]?.entries() ?? [])].sort((a, b) => b[1] - a[1]);
              if (!values.length) return null;
              return (
                <label key={f.key} className="flex flex-col gap-1">
                  <span className="text-[11px] uppercase tracking-wide text-fg-subtle">{f.label}</span>
                  <Select value={facetSel[f.key] ?? ''} className="min-w-[9rem]"
                    onChange={(e) => { setFacetSel((s) => ({ ...s, [f.key]: e.target.value })); setLimit(PAGE); }}>
                    <option value="">All · {rows.length}</option>
                    {values.map(([v, n]) => <option key={v} value={v}>{v} · {n}</option>)}
                  </Select>
                </label>
              );
            })}
            <label className="flex min-w-[12rem] flex-1 flex-col gap-1">
              <span className="text-[11px] uppercase tracking-wide text-fg-subtle">Search</span>
              <div className="relative">
                <Search className="pointer-events-none absolute left-2 top-2 h-3.5 w-3.5 text-fg-subtle" aria-hidden="true" />
                <input value={search} onChange={(e) => { setSearch(e.target.value); setLimit(PAGE); }} placeholder="task key or title…"
                  className="h-8 w-full rounded-md border border-border bg-canvas-inset pl-7 pr-2 text-xs text-fg outline-none focus:border-accent-fg" />
              </div>
            </label>
          </div>

          <div className="mb-2 flex items-center gap-2 text-xs">
            <Btn variant="outline" loading={busy} icon={<Ban className="h-3.5 w-3.5" />}
              disabled={filtered.length === 0}
              onClick={() => toggle(filtered.map((t) => t.taskKey), true)}>
              Disable {filtered.length}
            </Btn>
            <Btn variant="invisible" loading={busy} icon={<Check className="h-3.5 w-3.5" />}
              disabled={filtered.length === 0}
              onClick={() => toggle(filtered.map((t) => t.taskKey), false)}>
              Enable {filtered.length}
            </Btn>
            <span className="ml-auto tabular-nums text-fg-muted">
              {filtered.length} shown · {disabledCount} disabled
            </span>
          </div>

          <div className="max-h-96 overflow-auto rounded-md border border-border">
            <ul className="divide-y divide-border">
              {filtered.slice(0, limit).map((t) => (
                <li key={t.taskKey} className="flex items-center gap-2 px-2 py-1.5 text-xs hover:bg-neutral-subtle">
                  <Switch checked={!t.disabled}
                    onChange={(enabled) => toggle([t.taskKey], !enabled)}
                    label={`Run ${t.taskKey}`} />
                  <span className={`truncate font-mono text-xs ${t.disabled ? 'text-fg-subtle line-through' : 'text-fg'}`}
                    title={t.title || t.taskKey}>
                    {t.taskKey}
                  </span>
                  <span className="ml-auto flex shrink-0 items-center gap-1">
                    {facetChips(t, facets).map((chip) => (
                      <Chip key={chip.key} title={`${chip.label}: ${chip.value}`}>{chip.value}</Chip>
                    ))}
                  </span>
                </li>
              ))}
            </ul>
            {filtered.length > limit && (
              <button onClick={() => setLimit((l) => l + PAGE)} className="w-full py-1.5 text-xs text-accent-fg hover:bg-neutral-subtle">
                Show {Math.min(PAGE, filtered.length - limit)} more
              </button>
            )}
            {filtered.length === 0 && <p className="p-3 text-xs text-fg-subtle">No task matches.</p>}
          </div>
        </>
      )}
    </Panel>
  );
}
