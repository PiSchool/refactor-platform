'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { eventTone, summarize, useSessionEvents } from '@/lib/events';

function ts(iso?: string) {
  if (!iso) return '';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : d.toISOString().slice(11, 19);
}

/** The raw event stream, one row per line of the agent's events.jsonl. */
export function EventsFeed({ sessionId }: { sessionId: string }) {
  const events = useSessionEvents(sessionId);
  const [filter, setFilter] = useState('');
  const [hideNoise, setHideNoise] = useState(true);
  const boxRef = useRef<HTMLDivElement>(null);

  const shown = useMemo(() => {
    const q = filter.toLowerCase();
    return events.filter((ev) => {
      if (hideNoise && ev.type.startsWith('hook.')) return false;
      if (!q) return true;
      return ev.type.toLowerCase().includes(q) || summarize(ev).toLowerCase().includes(q);
    });
  }, [events, filter, hideNoise]);

  useEffect(() => {
    const el = boxRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [shown.length]);

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <div className="flex shrink-0 items-center gap-2">
        <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter events…"
          className="h-7 flex-1 rounded-md border border-border bg-canvas-inset px-2 text-xs text-fg" />
        <label className="flex shrink-0 items-center gap-1 text-[11px] text-fg-muted">
          <input type="checkbox" checked={hideNoise} onChange={(e) => setHideNoise(e.target.checked)} />
          hide hooks
        </label>
        <span className="shrink-0 text-[11px] text-fg-subtle">{shown.length}/{events.length}</span>
      </div>

      <div ref={boxRef} className="min-h-0 flex-1 overflow-auto rounded-md border border-border bg-canvas-inset">
        {shown.length === 0 ? (
          <p className="p-3 text-xs text-fg-subtle">{events.length ? 'No events match.' : 'No events recorded.'}</p>
        ) : (
          <table className="w-full border-collapse text-[11px]">
            <tbody>
              {shown.map((ev, i) => (
                <tr key={ev.id ?? i} className="align-top border-b border-border/50 last:border-0 hover:bg-neutral-subtle">
                  <td className="w-16 whitespace-nowrap px-2 py-1 font-mono text-fg-subtle">{ts(ev.timestamp)}</td>
                  <td className={`w-48 whitespace-nowrap px-2 py-1 font-mono ${eventTone(ev.type)}`}>{ev.type}</td>
                  <td className="break-all px-2 py-1 font-mono text-fg-muted">{summarize(ev)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
