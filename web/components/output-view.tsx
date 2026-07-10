'use client';

import { useEffect, useMemo, useState } from 'react';
import { StatusIcon } from '@/components/ui';
import { isProblem, stripAnsi, tone } from '@/lib/log';

interface LogEntry { stage: string; path: string; sizeBytes: number }

/** The engine writes `<stage>.log` with dots replaced by underscores. */
const fileStem = (stage: string) => stage.replace(/\./g, '_');

export function OutputView({ runId, taskId, stages }: {
  runId: string; taskId: string; stages?: Record<string, unknown>;
}) {
  const [logs, setLogs] = useState<LogEntry[] | null>(null);
  const [active, setActive] = useState('');
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [onlyProblems, setOnlyProblems] = useState(false);

  useEffect(() => {
    let stale = false;
    setLogs(null); setActive(''); setText('');
    fetch(`/api/runs/${runId}/tasks/${taskId}/logs`)
      .then((r) => (r.ok ? r.json() : { logs: [] }))
      .then((d) => {
        if (stale) return;
        setLogs(d.logs);
        if (d.logs.length) setActive(d.logs[0].stage);
      })
      .catch(() => { if (!stale) setLogs([]); });
    return () => { stale = true; };
  }, [runId, taskId]);

  const entry = logs?.find((l) => l.stage === active);

  useEffect(() => {
    if (!entry) { setText(''); return; }
    let stale = false;
    setLoading(true);
    fetch(`/api/artifact?path=${encodeURIComponent(entry.path)}`)
      .then((r) => (r.ok ? r.text() : `(unavailable: HTTP ${r.status})`))
      .then((t) => { if (!stale) setText(stripAnsi(t)); })
      .finally(() => { if (!stale) setLoading(false); });
    return () => { stale = true; };
  }, [entry?.path]);

  const lines = useMemo(() => {
    const all = text.split('\n');
    if (!onlyProblems) return all;
    return all.filter(isProblem);
  }, [text, onlyProblems]);

  if (!logs) return <p className="p-3 text-xs text-fg-subtle">Loading output…</p>;
  if (logs.length === 0) {
    return (
      <p className="p-3 text-xs text-fg-subtle">
        No build or test output yet. Evaluation writes it when the agent finishes.
      </p>
    );
  }

  /** stage status comes from the result, keyed by the un-normalized name */
  const statusOf = (stem: string): boolean | undefined => {
    const key = Object.keys(stages ?? {}).find((k) => fileStem(k) === stem);
    const stage = key ? (stages![key] as { ok?: boolean } | null) : null;
    return stage && typeof stage.ok === 'boolean' ? stage.ok : undefined;
  };

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <div className="flex shrink-0 flex-wrap items-center gap-1">
        {logs.map((l) => {
          const ok = statusOf(l.stage);
          return (
            <button key={l.stage} onClick={() => setActive(l.stage)}
              className={`flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs ${
                active === l.stage ? 'border-accent-fg bg-accent-subtle/30 text-fg' : 'border-border text-fg-muted hover:text-fg'}`}>
              {ok !== undefined && <StatusIcon status={ok ? 'passed' : 'failed'} className="h-3 w-3" />}
              <span className="font-mono">{l.stage}</span>
              <span className="text-[10px] text-fg-subtle">{(l.sizeBytes / 1024).toFixed(1)}kB</span>
            </button>
          );
        })}
        <label className="ml-auto flex items-center gap-1 text-[11px] text-fg-muted">
          <input type="checkbox" checked={onlyProblems} onChange={(e) => setOnlyProblems(e.target.checked)} />
          errors &amp; warnings only
        </label>
        {entry && (
          <a href={`/api/artifact?path=${encodeURIComponent(entry.path)}`} target="_blank" rel="noreferrer"
            className="text-[11px] text-accent-fg hover:underline">raw</a>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-border bg-canvas-inset">
        {loading ? <p className="p-3 text-xs text-fg-subtle">Loading…</p> : (
          <table className="w-full border-collapse font-mono text-[11px] leading-5">
            <tbody>
              {lines.map((l, i) => (
                <tr key={i} className="hover:bg-neutral-subtle">
                  <td className="w-12 select-none border-r border-border px-1 text-right align-top text-fg-subtle">{i + 1}</td>
                  <td className={`whitespace-pre-wrap break-all px-2 ${tone(l)}`}>{l || ' '}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && lines.length === 0 && (
          <p className="p-3 text-xs text-fg-subtle">{onlyProblems ? 'No errors or warnings.' : '(empty)'}</p>
        )}
      </div>
    </div>
  );
}
