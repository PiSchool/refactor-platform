'use client';

import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { useModels, useSettings, type ProviderModel } from '@/lib/api';
import { costUsd, formatTokens, formatUsd, type Usage } from '@/lib/cost';

/** What this task cost, and what the identical token usage would have cost on
 *  other models. Projections assume the same token counts — a different model
 *  would in reality take a different path, so this is a price comparison, not a
 *  performance prediction. */
export function CostPanel({ result }: { result: any }) {
  const { data: catalog } = useModels();
  const { data: settings } = useSettings();
  const [query, setQuery] = useState('');
  const [freeOnly, setFreeOnly] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const metrics = result?.metrics ?? {};
  const usage: Usage = {
    inputTokens: result?.tokensInput ?? 0,
    outputTokens: result?.tokensOutput ?? 0,
    cacheReadTokens: metrics.tokensCacheRead ?? 0,
  };

  const models = catalog?.models ?? [];
  const used = models.find((m) => m.id === result?.model);
  const actual = costUsd(usage, used);
  const projectionId = settings?.editable.costModel || '';
  const projection = models.find((m) => m.id === projectionId);
  const projected = projection ? costUsd(usage, projection) : null;

  const others = useMemo(() => {
    const q = query.trim().toLowerCase();
    return models
      .filter((m) => m.id !== result?.model)
      .filter((m) => (!freeOnly || m.free) && (!q || m.id.toLowerCase().includes(q) || m.name.toLowerCase().includes(q)))
      .map((m) => ({ model: m, cost: costUsd(usage, m) }))
      .filter((r) => r.cost != null)
      .sort((a, b) => (a.cost! - b.cost!))
      .slice(0, 40);
  }, [models, query, freeOnly, result?.model, usage.inputTokens, usage.outputTokens, usage.cacheReadTokens]);

  if (!result) return null;
  const total = usage.inputTokens + usage.outputTokens;

  return (
    <div className="rounded-md border border-border">
      <div className="flex items-center justify-between border-b border-border bg-canvas-subtle px-2 py-1.5">
        <span className="text-[11px] font-medium text-fg">Cost</span>
        <span className="font-mono text-[10px] tabular-nums text-fg-subtle">{formatTokens(total)} tokens</span>
      </div>

      <div className="space-y-1 px-2 py-1.5 text-[11px]">
        <Line label={used?.name ?? result.model} value={formatUsd(actual)} strong
          hint={used ? undefined : 'model not in the provider catalog'} />
        {projection && (
          <Line label={`projected · ${projection.name}`} value={formatUsd(projected)}
            delta={actual != null && projected != null ? projected - actual : null} />
        )}
        {metrics.tokensCacheRead > 0 && (
          <p className="text-[10px] text-fg-subtle">
            {formatTokens(metrics.tokensCacheRead)} of the prompt came from cache (billed lower).
          </p>
        )}
      </div>

      <button onClick={() => setExpanded((e) => !e)}
        className="w-full border-t border-border px-2 py-1 text-left text-[10px] text-accent-fg hover:bg-neutral-subtle">
        {expanded ? 'Hide' : 'Compare'} other models
      </button>

      {expanded && (
        <div className="border-t border-border p-2">
          <div className="mb-1.5 flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-2 top-1.5 h-3 w-3 text-fg-subtle" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter models…"
                className="h-6 w-full rounded border border-border bg-canvas-inset pl-6 pr-2 text-[11px] text-fg" />
            </div>
            <label className="flex shrink-0 items-center gap-1 text-[10px] text-fg-muted">
              <input type="checkbox" checked={freeOnly} onChange={(e) => setFreeOnly(e.target.checked)} />
              free
            </label>
          </div>

          <ul className="max-h-56 overflow-auto">
            {others.map(({ model, cost }) => (
              <li key={model.id} className="flex items-center gap-2 py-0.5 text-[11px]">
                <span className="truncate font-mono text-[10px] text-fg-muted">{model.id}</span>
                <span className="ml-auto shrink-0 font-mono tabular-nums text-fg">{formatUsd(cost)}</span>
              </li>
            ))}
            {others.length === 0 && <li className="py-1 text-[11px] text-fg-subtle">No priced models match.</li>}
          </ul>
          <p className="mt-1 text-[10px] text-fg-subtle">
            Same token counts, different prices — a comparison, not a prediction of how another model would behave.
          </p>
        </div>
      )}
    </div>
  );
}

function Line({ label, value, strong, delta, hint }: {
  label: string; value: string; strong?: boolean; delta?: number | null; hint?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="min-w-0 truncate text-fg-muted">
        {label}
        {hint && <span className="ml-1 text-[10px] text-fg-subtle">({hint})</span>}
      </span>
      <span className="flex shrink-0 items-center gap-1.5">
        {delta != null && delta !== 0 && (
          <span className={`font-mono text-[10px] tabular-nums ${delta > 0 ? 'text-danger-fg' : 'text-success-fg'}`}>
            {delta > 0 ? '+' : '−'}{formatUsd(Math.abs(delta)).replace('$', '$')}
          </span>
        )}
        <span className={`font-mono tabular-nums ${strong ? 'text-fg' : 'text-fg-muted'}`}>{value}</span>
      </span>
    </div>
  );
}
