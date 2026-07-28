'use client';

import { Archive } from 'lucide-react';
import { useState } from 'react';
import { useRuns, useRunAction } from '@/lib/api';
import { Btn, Card, Select, SkeletonRow, EmptyState } from '@/components/ui';
import { ImportRun } from '@/components/import-run';
import { RunRow } from '@/components/run-list-row';
import { isArchived } from '@/lib/utils';

const STATUSES = ['', 'running', 'queued', 'completed', 'failed', 'stopped'];

export default function RunsPage() {
  const [status, setStatus] = useState('');
  const [q, setQ] = useState('');
  const [showArchived, setShowArchived] = useState(true);
  const { data, isLoading } = useRuns({ status: status || undefined });
  const { restart, stop, del } = useRunAction();

  const runs = (data?.runs || []).filter((r) =>
    !q || r.id.includes(q) || r.model.includes(q) || r.benchmark.name.toLowerCase().includes(q.toLowerCase()));
  const live = runs.filter((r) => !isArchived(r));
  const archived = runs.filter(isArchived);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-lg font-semibold text-fg">Workflow runs</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowArchived((v) => !v)}
            className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 h-8 text-xs ${showArchived ? 'border-accent-muted bg-accent-subtle text-accent-fg' : 'border-border text-fg-muted hover:text-fg'}`}>
            <Archive className="h-3.5 w-3.5" /> Archived {archived.length > 0 && `(${archived.length})`}
          </button>
          <ImportRun />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search runs…"
          className="h-8 w-64 rounded-md border border-border bg-canvas-inset px-3 text-sm text-fg placeholder:text-fg-subtle focus:border-accent-fg focus:outline-none"
        />
        <Select value={status} onChange={(e) => setStatus(e.target.value)}>
          {STATUSES.map((s) => <option key={s} value={s}>{s ? s[0].toUpperCase() + s.slice(1) : 'All statuses'}</option>)}
        </Select>
        {(q || status) && <Btn variant="invisible" onClick={() => { setQ(''); setStatus(''); }}>Clear</Btn>}
      </div>

      <Card className="divide-y divide-border">
        {isLoading ? (
          <div className="p-3 space-y-2">{Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)}</div>
        ) : runs.length === 0 ? (
          <EmptyState title={q || status ? 'No matching runs' : 'No runs yet'} />
        ) : (
          <>
            {live.map((r) => (
              <RunRow key={r.id} r={r} archived={false}
                restart={restart.mutate} stop={stop.mutate} del={del.mutate} />
            ))}
            {showArchived && archived.length > 0 && (
              <div className="flex items-center gap-2 bg-canvas-subtle/60 px-3 py-1.5 text-[11px] font-medium uppercase tracking-wide text-fg-subtle">
                <Archive className="h-3 w-3" /> Study archive — published results.
              </div>
            )}
            {showArchived && archived.map((r) => (
              <RunRow key={r.id} r={r} archived
                restart={restart.mutate} stop={stop.mutate} del={del.mutate} />
            ))}
          </>
        )}
      </Card>
    </div>
  );
}
