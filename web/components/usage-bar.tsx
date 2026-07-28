'use client';

import { useMemo } from 'react';
import { Coins, Gauge, Layers } from 'lucide-react';
import { useModels, useSettings } from '@/lib/api';
import { liveUsage, useSessionEvents } from '@/lib/events';
import { costUsd, formatTokens, formatUsd } from '@/lib/cost';
import { Tooltip } from '@/components/ui';

/** Usage bar over the agent view.
 *
 *  Shows only what the agent actually measured. Output tokens, turns and
 *  compactions stream live. Prompt tokens, context occupancy and therefore cost
 *  exist only in `session.shutdown`, so they appear when the session ends —
 *  never as an extrapolation from message sizes.
 */
export function UsageBar({ sessionId, model }: { sessionId: string; model: string }) {
  const events = useSessionEvents(sessionId);
  const { data: catalog } = useModels();
  const { data: settings } = useSettings();

  const usage = useMemo(() => liveUsage(events), [events]);
  const models = catalog?.models ?? [];
  const used = models.find((m) => m.id === model);
  const projection = models.find((m) => m.id === (settings?.editable.costModel || ''));

  if (!events.length) return null;

  const { final } = usage;
  const window = used?.contextLength ?? null;
  const pct = final && window ? Math.min(100, (final.contextTokens / window) * 100) : null;
  const nearLimit = pct != null && pct >= 80;

  const tokens = final && { inputTokens: final.inputTokens, outputTokens: usage.outputTokens, cacheReadTokens: final.cacheReadTokens };
  const spend = tokens ? costUsd(tokens, used) : null;
  const projected = tokens && projection ? costUsd(tokens, projection) : null;

  return (
    <div className="shrink-0 rounded-md border border-border bg-canvas-subtle px-3 py-2">
      <div className="flex items-center gap-2 text-xs">
        <Gauge className="h-3.5 w-3.5 shrink-0 text-fg-muted" />
        <span className="text-fg-muted">Context</span>
        {final ? (
          <span className={`font-mono tabular-nums ${nearLimit ? 'text-attention-fg' : 'text-fg'}`}>
            {formatTokens(final.contextTokens)}
            {window && <span className="text-fg-subtle"> / {formatTokens(window)}</span>}
          </span>
        ) : (
          <span className="text-fg-subtle">
            not reported until the session ends
            {window && <span className="font-mono"> · window {formatTokens(window)}</span>}
          </span>
        )}
        {pct != null && <span className="ml-auto font-mono tabular-nums text-fg-subtle">{pct.toFixed(0)}%</span>}
        {usage.compactions > 0 && (
          <Tooltip content="The agent compacted its context to keep going">
            <span className="flex items-center gap-1 rounded-full bg-attention-subtle px-1.5 text-[11px] text-attention-fg">
              <Layers className="h-3 w-3" />{usage.compactions}
            </span>
          </Tooltip>
        )}
      </div>

      {pct != null && (
        <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-neutral-subtle">
          <div className={`h-full rounded-full ${nearLimit ? 'bg-attention-fg' : 'bg-accent-fg'}`} style={{ width: `${pct}%` }} />
        </div>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
        <span className="text-fg-muted">
          turns <span className="font-mono tabular-nums text-fg">{usage.turns}</span>
        </span>
        <span className="text-fg-muted">
          out <span className="font-mono tabular-nums text-fg">{formatTokens(usage.outputTokens)}</span>
        </span>
        {final && (
          <span className="text-fg-muted">
            in <span className="font-mono tabular-nums text-fg">{formatTokens(final.inputTokens)}</span>
            {final.cacheReadTokens > 0 && (
              <span className="text-fg-subtle"> ({formatTokens(final.cacheReadTokens)} cached)</span>
            )}
          </span>
        )}

        {final && (
          <span className="ml-auto flex items-center gap-1.5">
            <Coins className="h-3.5 w-3.5 shrink-0 text-fg-muted" />
            <span className="text-fg-muted">cost</span>
            <span className="font-mono tabular-nums text-fg">{used?.free ? 'free' : formatUsd(spend)}</span>
            {projection && (
              <Tooltip content={`The same token counts priced on ${projection.name}`}>
                <span className="font-mono tabular-nums text-fg-subtle">
                  → {formatUsd(projected)} on {projection.id.split('/').pop()}
                </span>
              </Tooltip>
            )}
          </span>
        )}
      </div>

      {!final && (
        <p className="mt-1 text-[11px] text-fg-subtle">
          The agent reports prompt tokens and context occupancy only when the session ends; cost follows from them.
        </p>
      )}
    </div>
  );
}
