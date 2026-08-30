'use client';

import Link from 'next/link';
import { Archive } from 'lucide-react';
import { Btn, LiveDot, StatusIcon } from '@/components/ui';
import { formatRelative, runOutcome } from '@/lib/utils';
import type { RunSummary } from '@/lib/types';

function summaryLine(run: RunSummary) {
  return [run.benchmark.name, run.setup.name, run.model].filter(Boolean).join(' · ');
}

export function RunRow({ r, archived, restart, stop, del }: {
  r: RunSummary;
  archived: boolean;
  restart: (id: string) => void;
  stop: (id: string) => void;
  del: (id: string) => void;
}) {
  return (
    <div className={`group flex items-center gap-3 px-3 py-2.5 hover:bg-neutral-subtle ${archived ? 'border-l-2 border-l-accent-muted bg-canvas-subtle/40' : ''}`}>
      <StatusIcon status={runOutcome(r)} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Link href={`/runs/${r.id}`} className="font-mono text-sm text-accent-fg hover:underline">{r.id.slice(0, 8)}</Link>
          {['running', 'queued'].includes(r.status) && <span className="inline-flex items-center gap-1 rounded-full bg-attention-subtle px-1.5 text-[11px] text-attention-fg"><LiveDot /> live</span>}
          {archived && (
            <span title={String(r.config?.title ?? 'Imported from the study archive')}
              className="inline-flex items-center gap-1 rounded-full border border-accent-muted bg-accent-subtle px-1.5 text-[11px] text-accent-fg">
              <Archive className="h-2.5 w-2.5" /> study archive
            </span>
          )}
        </div>
        <p className="truncate text-xs text-fg-muted">
          {archived && r.config?.title ? String(r.config.title) : summaryLine(r)} · {r.counts.passed}/{r.counts.total} passed
        </p>
      </div>
      <span className="text-xs text-fg-subtle">{formatRelative(r.finishedAt || r.startedAt || r.queuedAt || undefined)}</span>
      <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <a href={`/api/runs/${r.id}/export`} title="Download full ZIP (summary, per-task metrics, artifacts)"><Btn variant="invisible">ZIP</Btn></a>
        {!archived && ['completed', 'failed', 'stopped'].includes(r.status) && <Btn variant="invisible" onClick={() => restart(r.id)}>Restart</Btn>}
        {['running', 'queued'].includes(r.status) && <Btn variant="invisible" onClick={() => stop(r.id)}>Stop</Btn>}
        {!['running', 'queued'].includes(r.status) && <Btn variant="invisible" onClick={() => del(r.id)}>Delete</Btn>}
      </div>
    </div>
  );
}