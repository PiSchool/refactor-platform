'use client';

import { useEffect, useState } from 'react';
import { Elapsed, StatusIcon } from '@/components/ui';
import { formatDurationSeconds } from '@/lib/utils';

interface Stage { ok?: boolean; message?: string }

function isCompletedStage(value: unknown): value is Stage {
  return typeof value === 'object' && value !== null && typeof (value as Stage).ok === 'boolean';
}

/** The verify pipeline the benchmark will run. Fetched so the checks are on
 *  screen from the start, pending, instead of "evaluation runs later". */
function usePlannedChecks(benchmarkKey: string) {
  const [stages, setStages] = useState<string[]>([]);
  useEffect(() => {
    let stale = false;
    fetch(`/api/benchmarks/${benchmarkKey}/evaluation`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (stale || !d) return;
        setStages(d.effective.verify.filter((s: any) => s.enabled).map((s: any) => s.preset));
      })
      .catch(() => {});
    return () => { stale = true; };
  }, [benchmarkKey]);
  return stages;
}

export function ChecksPanel({ benchmarkKey, task }: { benchmarkKey: string; task: any }) {
  const planned = usePlannedChecks(benchmarkKey);
  const details: Record<string, unknown> = task?.result?.details ?? {};
  const evaluated = Object.entries(details).filter(
    (entry): entry is [string, Stage] => isCompletedStage(entry[1]),
  );

  // Result details also contain benchmark metadata and provenance. Only actual
  // verification stages have an `ok` verdict and belong in the checks list.
  const rows = task?.result
    ? evaluated
    : planned.map((name) => [name, {} as Stage] as [string, Stage]);

  if (rows.length === 0) return null;

  const passing = rows.filter(([, v]) => v.ok === true).length;
  const scored = rows.filter(([, v]) => typeof v.ok === 'boolean').length;

  const agentSeconds = task?.result?.agentSeconds;
  const evalSeconds = task?.result?.evaluateSeconds;
  // While the task is running the agent still holds the clock: evaluation only
  // starts once the agent process exits, so it is pending, not "running".
  const running = task?.status === 'running';

  return (
    <div className="rounded-md border border-border">
      <div className="flex items-center justify-between border-b border-border bg-canvas-subtle px-2 py-1.5">
        <span className="text-xs font-medium text-fg">Checks</span>
        <span className="text-[11px] text-fg-subtle">
          {scored > 0 ? `${passing}/${rows.length} passing` : `${rows.length} pending`}
        </span>
      </div>

      <ul className="divide-y divide-border">
        {rows.map(([name, stage]) => <Check key={name} name={name} stage={stage} />)}
      </ul>

      {/* where the wall-clock went */}
      <div className="flex items-center justify-between border-t border-border px-2 py-1.5 text-[11px] text-fg-subtle">
        <span>
          Agent{' '}
          <span className="tabular-nums text-fg-muted">
            {agentSeconds != null
              ? formatDurationSeconds(agentSeconds)
              : running
              ? <Elapsed startedAt={task.startedAt} finishedAt={task.finishedAt} />
              : '—'}
          </span>
        </span>
        <span>
          Evaluation{' '}
          <span className="tabular-nums text-fg-muted">
            {evalSeconds != null ? formatDurationSeconds(evalSeconds) : running ? 'pending' : '—'}
          </span>
        </span>
      </div>

      {task?.result?.reason && (
        <div className="border-t border-border px-2 py-1.5">
          <span className="text-[11px] uppercase tracking-wide text-fg-subtle">Reason</span>
          <p className="font-mono text-xs text-danger-fg">{task.result.reason}</p>
        </div>
      )}
    </div>
  );
}

/** One evaluation stage, rendered like a GitHub check run. */
function Check({ name, stage }: { name: string; stage: Stage }) {
  const pending = typeof stage.ok !== 'boolean';
  return (
    <li className="flex items-start gap-1.5 px-2 py-1.5">
      <StatusIcon status={pending ? 'pending' : stage.ok ? 'passed' : 'failed'} className="mt-0.5 h-3.5 w-3.5" />
      <div className="min-w-0 flex-1">
        <p className={`font-mono text-xs ${pending ? 'text-fg-muted' : 'text-fg'}`}>{name}</p>
        <p className="break-words text-[11px] text-fg-subtle">
          {stage.message || (pending ? 'Waiting for the agent to finish.' : '')}
        </p>
      </div>
    </li>
  );
}
