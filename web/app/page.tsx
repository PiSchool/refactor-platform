'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Activity } from 'lucide-react';
import { useOverview, useRunAction } from '@/lib/api';
import { Btn, Card, LiveDot, SkeletonCard, StatusIcon, EmptyState } from '@/components/ui';
import { RunWizard } from '@/components/run-wizard';
import { NewRunButton } from '@/components/run-management-actions';
import { formatRelative, runOutcome } from '@/lib/utils';
import type { RunSummary } from '@/lib/types';

function summaryLine(r: RunSummary) {
  return [r.benchmark.name, r.model, r.setup.name].filter(Boolean).join(' · ');
}

export default function OverviewPage() {
  const { data, isLoading } = useOverview();
  const [wizard, setWizard] = useState(false);
  const { stop } = useRunAction();

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-fg-muted" />
          <h1 className="text-lg font-semibold text-fg">Workflows</h1>
        </div>
        <NewRunButton onClick={() => setWizard(true)} />
      </div>

      {isLoading ? (
        <SkeletonCard rows={4} />
      ) : !data || data.runsTotal === 0 ? (
        <EmptyState title="No runs yet"
          description="Launch a benchmark run to get started."
          action={<NewRunButton onClick={() => setWizard(true)} />} />
      ) : (
        <>
          <div className="flex items-center gap-4 text-sm text-fg-muted">
            <span>{data.runsTotal} runs</span>
            {data.runningCount > 0 && (
              <span className="inline-flex items-center gap-1.5 text-success-fg">
                <LiveDot /> {data.runningCount} running
              </span>
            )}
          </div>

          {data.activeRuns.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2">
              {data.activeRuns.map((r) => (
                <Card key={r.id} className="border-attention-muted/40 bg-attention-subtle/30 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <StatusIcon status={runOutcome(r)} />
                        <Link href={`/runs/${r.id}`} className="font-mono text-sm text-accent-fg hover:underline">
                          {r.id.slice(0, 8)}
                        </Link>
                        <LiveDot />
                      </div>
                      <p className="mt-1 truncate text-xs text-fg-muted">{summaryLine(r)}</p>
                      <p className="mt-1 text-xs text-fg-subtle">
                        {r.counts.passed + r.counts.failed + r.counts.timedOut}/{r.counts.total} tasks
                      </p>
                    </div>
                    <Btn variant="danger" onClick={() => stop.mutate(r.id)}>Stop</Btn>
                  </div>
                </Card>
              ))}
            </div>
          )}

          <Card className="divide-y divide-border">
            <div className="flex items-center justify-between px-3 py-2">
              <h2 className="text-sm font-semibold text-fg">Recent runs</h2>
              <Link href="/runs" className="text-xs text-accent-fg hover:underline">View all →</Link>
            </div>
            {data.recentRuns.slice(0, 8).map((r) => (
              <Link key={r.id} href={`/runs/${r.id}`} className="flex items-center gap-3 px-3 py-2 hover:bg-neutral-subtle">
                <StatusIcon status={runOutcome(r)} />
                <span className="font-mono text-xs text-accent-fg">{r.id.slice(0, 8)}</span>
                <span className="min-w-0 flex-1 truncate text-xs text-fg-muted">{summaryLine(r)}</span>
                <span className="text-xs text-fg-subtle">{formatRelative(r.finishedAt || r.startedAt || r.queuedAt || undefined)}</span>
              </Link>
            ))}
          </Card>
        </>
      )}

      {wizard && <RunWizard onClose={() => setWizard(false)} />}
    </div>
  );
}
