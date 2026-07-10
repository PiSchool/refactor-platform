'use client';

import { useMemo, useState } from 'react';
import { Check, ChevronDown, Search } from 'lucide-react';
import { useModels, type ProviderModel } from '@/lib/api';
import { formatTokens } from '@/lib/cost';

/** Price per million prompt tokens — the unit people actually compare. */
function perMillion(m: ProviderModel): string {
  const p = Number(m.pricing?.prompt ?? NaN);
  const c = Number(m.pricing?.completion ?? NaN);
  if (!Number.isFinite(p) || !Number.isFinite(c)) return 'price n/a';
  if (p < 0 || c < 0) return 'price varies';   // router models publish -1
  if (p === 0 && c === 0) return 'free';
  return `$${(p * 1e6).toFixed(2)} / $${(c * 1e6).toFixed(2)} per M`;
}

/** Searchable dropdown over the live provider catalog. Falls back to a text
 *  field when the catalog is unreachable, so the platform stays usable offline. */
export function ModelPicker({ value, onChange, allowEmpty = false, placeholder = 'provider/model-id' }: {
  value: string;
  onChange: (id: string) => void;
  allowEmpty?: boolean;
  placeholder?: string;
}) {
  const { data } = useModels();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [freeOnly, setFreeOnly] = useState(false);

  const models = data?.models ?? [];
  const live = data?.source === 'provider' || data?.source === 'cache';

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return models
      .filter((m) => (!freeOnly || m.free) && (!q || m.id.toLowerCase().includes(q) || m.name.toLowerCase().includes(q)))
      .slice(0, 120);
  }, [models, query, freeOnly]);

  if (!live) {
    return (
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="h-8 w-72 rounded-md border border-border bg-canvas-inset px-3 text-sm text-fg" />
    );
  }

  const selected = models.find((m) => m.id === value);

  return (
    <div className="relative w-72">
      <button type="button" onClick={() => setOpen((o) => !o)}
        className="flex h-8 w-full items-center gap-2 rounded-md border border-border bg-canvas-inset px-3 text-left text-sm text-fg">
        <span className="truncate">{value || <span className="text-fg-subtle">Select a model…</span>}</span>
        {selected?.free && <span className="shrink-0 rounded bg-success-subtle px-1 text-[10px] text-success-fg">free</span>}
        <ChevronDown className="ml-auto h-3.5 w-3.5 shrink-0 text-fg-muted" />
      </button>

      {open && (
        <div className="absolute z-30 mt-1 w-[26rem] rounded-md border border-border bg-canvas shadow-lg">
          <div className="flex items-center gap-2 border-b border-border p-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-2 top-2 h-3.5 w-3.5 text-fg-subtle" />
              <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search models…"
                className="h-7 w-full rounded border border-border bg-canvas-inset pl-7 pr-2 text-xs text-fg" />
            </div>
            <label className="flex shrink-0 items-center gap-1 text-[11px] text-fg-muted">
              <input type="checkbox" checked={freeOnly} onChange={(e) => setFreeOnly(e.target.checked)} />
              free
            </label>
          </div>

          <ul className="max-h-72 overflow-auto">
            {allowEmpty && (
              <li>
                <button onClick={() => { onChange(''); setOpen(false); }}
                  className="flex w-full items-center gap-2 px-2 py-1.5 text-left text-xs text-fg-muted hover:bg-neutral-subtle">
                  {value === '' && <Check className="h-3 w-3" />}
                  <span className={value === '' ? '' : 'ml-5'}>None</span>
                </button>
              </li>
            )}
            {shown.map((m) => (
              <li key={m.id}>
                <button onClick={() => { onChange(m.id); setOpen(false); }}
                  className="flex w-full items-center gap-2 px-2 py-1.5 text-left hover:bg-neutral-subtle">
                  {value === m.id ? <Check className="h-3 w-3 shrink-0 text-accent-fg" /> : <span className="w-3 shrink-0" />}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs text-fg">{m.name}</p>
                    <p className="truncate font-mono text-[10px] text-fg-subtle">{m.id}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className={`text-[10px] ${m.free ? 'text-success-fg' : 'text-fg-muted'}`}>{perMillion(m)}</p>
                    {m.contextLength && <p className="text-[10px] text-fg-subtle">{formatTokens(m.contextLength)} ctx</p>}
                  </div>
                </button>
              </li>
            ))}
            {shown.length === 0 && <li className="p-3 text-xs text-fg-subtle">No models match.</li>}
          </ul>
          <div className="border-t border-border px-2 py-1 text-[10px] text-fg-subtle">
            {models.length} models · prices live from the provider
          </div>
        </div>
      )}
    </div>
  );
}
