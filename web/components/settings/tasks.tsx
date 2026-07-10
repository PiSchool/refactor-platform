'use client';

import { useEffect, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { Btn } from '@/components/ui';
import { useCatalog } from '@/lib/api';
import { getJson, Note, Panel } from './kit';

interface TaskRow { taskKey: string; title: string; params: Record<string, any>; disabled: boolean }
const PAGE = 100;

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
    <Panel title="Tasks" description="Disabled tasks are hidden from the run wizard and rejected at run creation.">
      {!rows ? <Note>Loading…</Note> : (
        <>
          <div className="mb-2 flex flex-wrap items-end gap-2">
            {facets.map((f) => {
              const values = [...(facetValues[f.key]?.entries() ?? [])].sort((a, b) => b[1] - a[1]);
              if (!values.length) return null;
              return (
                <label key={f.key} className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-fg-subtle">{f.label}</span>
                  <select value={facetSel[f.key] ?? ''} onChange={(e) => { setFacetSel((s) => ({ ...s, [f.key]: e.target.value })); setLimit(PAGE); }}
                    className="h-8 min-w-[9rem] rounded-md border border-border bg-canvas-inset px-2 text-xs text-fg">
                    <option value="">All ({rows.length})</option>
                    {values.map(([v, n]) => <option key={v} value={v}>{v} ({n})</option>)}
                  </select>
                </label>
              );
            })}
            <label className="flex min-w-[12rem] flex-1 flex-col gap-1">
              <span className="text-[10px] uppercase tracking-wide text-fg-subtle">Search</span>
              <div className="relative">
                <Search className="pointer-events-none absolute left-2 top-2 h-3.5 w-3.5 text-fg-subtle" />
                <input value={search} onChange={(e) => { setSearch(e.target.value); setLimit(PAGE); }} placeholder="task key…"
                  className="h-8 w-full rounded-md border border-border bg-canvas-inset pl-7 pr-2 text-xs text-fg" />
              </div>
            </label>
          </div>

          <div className="mb-2 flex items-center gap-2 text-xs">
            <Btn variant="outline" loading={busy} onClick={() => toggle(filtered.map((t) => t.taskKey), true)}>
              Disable {filtered.length} matching
            </Btn>
            <Btn variant="invisible" loading={busy} onClick={() => toggle(filtered.map((t) => t.taskKey), false)}>Enable matching</Btn>
            <span className="ml-auto text-fg-muted">{disabledCount} disabled · {filtered.length} match</span>
          </div>

          <div className="max-h-96 overflow-auto rounded-md border border-border">
            <ul className="divide-y divide-border">
              {filtered.slice(0, limit).map((t) => (
                <li key={t.taskKey} className="flex items-center gap-2 px-2 py-1.5 text-xs hover:bg-neutral-subtle">
                  <input type="checkbox" checked={!t.disabled} onChange={(e) => toggle([t.taskKey], !e.target.checked)} />
                  <span className={`truncate font-mono text-[11px] ${t.disabled ? 'text-fg-subtle line-through' : 'text-fg'}`}>{t.taskKey}</span>
                  <span className="ml-auto shrink-0 text-[10px] text-fg-subtle">{t.params?.refactoringType ?? t.params?.mode ?? ''}</span>
                </li>
              ))}
            </ul>
            {filtered.length > limit && (
              <button onClick={() => setLimit((l) => l + PAGE)} className="w-full py-1.5 text-xs text-accent-fg hover:bg-neutral-subtle">
                Show {Math.min(PAGE, filtered.length - limit)} more
              </button>
            )}
            {filtered.length === 0 && <p className="p-3 text-xs text-fg-subtle">No tasks match.</p>}
          </div>
        </>
      )}
    </Panel>
  );
}
