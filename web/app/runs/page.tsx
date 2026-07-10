'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRuns, useRunAction } from '@/lib/api';
import { Btn, Card, LiveDot, Select, SkeletonRow, StatusIcon, EmptyState } from '@/components/ui';
import { formatDurationSeconds, formatRelative, runOutcome } from '@/lib/utils';
import type { RunSummary } from '@/lib/types';

const STATUSES = ['', 'running', 'queued', 'completed', 'failed', 'stopped'];

function summaryLine(r: RunSummary) {
  return [r.benchmark.name, r.setup.name, r.model].filter(Boolean).join(' · ');
}

export default function RunsPage() {
  const [status, setStatus] = useState('');
  const [q, setQ] = useState('');
  const { data, isLoading } = useRuns({ status: status || undefined });
  const { restart, stop, del } = useRunAction();

  const runs = (data?.runs || []).filter((r) =>
    !q || r.id.includes(q) || r.model.includes(q) || r.benchmark.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold text-fg">Workflow runs</h1>

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
        ) : runs.map((r) => (
          <div key={r.id} className="group flex items-center gap-3 px-3 py-2.5 hover:bg-neutral-subtle">
            <StatusIcon status={runOutcome(r)} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <Link href={`/runs/${r.id}`} className="font-mono text-sm text-accent-fg hover:underline">{r.id.slice(0, 8)}</Link>
                {['running', 'queued'].includes(r.status) && <span className="inline-flex items-center gap-1 rounded-full bg-attention-subtle px-1.5 text-[10px] text-attention-fg"><LiveDot /> live</span>}
              </div>
              <p className="truncate text-xs text-fg-muted">{summaryLine(r)} · {r.counts.passed}/{r.counts.total} passed</p>
            </div>
            <span className="text-xs text-fg-subtle">{formatRelative(r.finishedAt || r.startedAt || r.queuedAt || undefined)}</span>
            <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              {['completed', 'failed', 'stopped'].includes(r.status) && <Btn variant="invisible" onClick={() => restart.mutate(r.id)}>Restart</Btn>}
              {['running', 'queued'].includes(r.status) && <Btn variant="invisible" onClick={() => stop.mutate(r.id)}>Stop</Btn>}
              {!['running', 'queued'].includes(r.status) && <Btn variant="invisible" onClick={() => del.mutate(r.id)}>Delete</Btn>}
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
