'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ListTree, Terminal as TerminalIcon,
} from 'lucide-react';
import { fetchArtifactText, findArtifact, useRun, useRunAction } from '@/lib/api';
import { Btn, Card, Elapsed, ProgressBar, StatusBadge, StatusIcon, SkeletonCard } from '@/components/ui';
import { Terminal } from '@/components/terminal';
import { EventsFeed } from '@/components/events-feed';
import { StepsView } from '@/components/steps-view';
import { RepositoryView } from '@/components/repository-view';
import { OutputView } from '@/components/output-view';
import { ChecksPanel } from '@/components/checks-panel';
import { UsageBar } from '@/components/usage-bar';
import { CostPanel } from '@/components/cost-panel';
import { RunHeaderActions, SkipTaskAction } from '@/components/run-management-actions';
import { formatDurationSeconds, runOutcome } from '@/lib/utils';
import type { ArtifactRef } from '@/lib/types';

const TABS = ['Agent', 'Repository', 'Output', 'Prompt', 'Retrieval', 'Events'] as const;
type Tab = (typeof TABS)[number];

/** Which artifact backs each text tab. Repository/Output are served live. */
const ARTIFACT: Partial<Record<Tab, string>> = {
  Prompt: 'prompt',
  Retrieval: 'retrieval-context',
};

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: run, isLoading } = useRun(id);
  const { stop, restart, del, skip } = useRunAction();
  const [selected, setSelected] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('Agent');
  const [agentView, setAgentView] = useState<'steps' | 'terminal'>('terminal');
  const [text, setText] = useState('');
  const [loadingText, setLoadingText] = useState(false);

  const tasks = run?.tasks || [];
  const current = tasks.find((t) => t.id === selected) || tasks[0];
  const live = ['running', 'queued'].includes(run?.status || '');
  const s3 = run?.setup.key === 's3';
  const s2 = run?.setup.key.startsWith('s2_') ?? false;
  const visibleTabs = s2 ? TABS : TABS.filter((item) => item !== 'Retrieval');
  const textArtifact = current ? findArtifact(current.artifacts, ARTIFACT[tab] ?? '') : undefined;
  const terminalArtifact = current?.session
    ? findArtifact(current.session.artifacts, 'terminal')
    : undefined;

  useEffect(() => { if (!selected && tasks[0]) setSelected(tasks[0].id); }, [tasks, selected]);

  // While a task is running the terminal is the live view; once it finishes the
  // steps (parsed transcript) are the useful view. Switch with the task's state
  // and when the selected task changes; manual toggles hold until the next change.
  useEffect(() => {
    if (current) setAgentView(current.status === 'running' ? 'terminal' : 'steps');
  }, [current?.status, current?.id]);

  useEffect(() => {
    setText('');
    if (!textArtifact) return;
    let stale = false;
    setLoadingText(true);
    fetchArtifactText(textArtifact)
      .then((t) => { if (!stale) setText(t); })
      .catch((e) => { if (!stale) setText(`(failed to load: ${e})`); })
      .finally(() => { if (!stale) setLoadingText(false); });
    return () => { stale = true; };
  }, [textArtifact?.viewUrl]);

  if (isLoading || !run) return <SkeletonCard rows={6} />;

  return (
    // Fill the viewport below the header, and let each column scroll on its own.
    <div className="flex h-[calc(100vh-3rem)] min-h-0 flex-col gap-3 lg:h-[calc(100vh-3rem)]">
      {/* ── run header ─────────────────────────────────────────────────── */}
      <div className="shrink-0 border-b border-border pb-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <StatusBadge status={runOutcome(run)} />
            <Link href="/runs" className="text-xs text-fg-muted hover:text-fg">runs /</Link>
            <span className="font-mono text-sm text-fg">{run.id.slice(0, 8)}</span>
            <Elapsed startedAt={run.startedAt} finishedAt={run.finishedAt} className="text-xs text-fg-muted" />
          </div>
          <RunHeaderActions runId={run.id} live={live}
            stopping={live && (stop.isPending || stop.isSuccess)}
            onRestart={() => restart.mutate(run.id)} onStop={() => stop.mutate(run.id)}
            onDelete={() => del.mutate(run.id)} />
        </div>
        <p className="mt-1 text-xs text-fg-muted">
          {run.agentTool.name} · {run.model} · {run.benchmark.name} · {run.setup.name}
        </p>
      </div>

      {/* ── three columns, each independently scrollable ───────────────── */}
      <div className="grid min-h-0 flex-1 gap-3 lg:grid-cols-[260px_1fr_320px]">
        {/* Jobs */}
        <Card className="flex min-h-0 flex-col">
          <div className="shrink-0 border-b border-border px-3 py-2 text-xs font-semibold text-fg">
            Jobs <span className="text-fg-subtle">({tasks.length})</span>
          </div>
          <div className="min-h-0 flex-1 divide-y divide-border overflow-auto">
            {tasks.map((t) => (
              <button key={t.id} onClick={() => setSelected(t.id)}
                className={`flex w-full items-center gap-2 px-3 py-2 text-left ${current?.id === t.id ? 'bg-neutral-subtle' : 'hover:bg-neutral-subtle'}`}>
                <StatusIcon status={t.status} />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-mono text-xs text-fg">{t.taskKey}</p>
                  <p className="text-[11px] text-fg-subtle">
                    {t.result
                      ? `${formatDurationSeconds(t.result.durationSeconds)} · ${t.result.tokensInput + t.result.tokensOutput} tok`
                      : t.status === 'running'
                      ? <>running · <Elapsed startedAt={t.startedAt} finishedAt={t.finishedAt} /></>
                      : t.status}
                  </p>
                </div>
                {live && current?.id === t.id && t.status === 'running' && (
                  <SkipTaskAction onSkip={() => skip.mutate({ runId: run.id, taskId: t.id })} />
                )}
              </button>
            ))}
          </div>
        </Card>

        {/* Session viewer */}
        <Card className="flex min-h-0 flex-col">
          <div className="flex shrink-0 items-center gap-1 border-b border-border px-2 py-1.5">
            {visibleTabs.map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`rounded px-2 py-1 text-xs ${tab === t ? 'bg-neutral-subtle text-fg' : 'text-fg-muted hover:text-fg'}`}>
                {t === 'Agent' && s3 ? 'Copilot · sub-agents' : t}
              </button>
            ))}
            {tab === 'Agent' && (
              <div className="ml-auto flex items-center gap-0.5 rounded-md border border-border p-0.5">
                <ToggleBtn active={agentView === 'steps'} onClick={() => setAgentView('steps')} icon={<ListTree className="h-3 w-3" />}>Steps</ToggleBtn>
                <ToggleBtn active={agentView === 'terminal'} onClick={() => setAgentView('terminal')} icon={<TerminalIcon className="h-3 w-3" />}>Terminal</ToggleBtn>
              </div>
            )}
          </div>

          <div className="min-h-0 flex-1 overflow-hidden p-2">
            {!current?.session ? (
              <p className="p-3 text-xs text-fg-subtle">No session yet.</p>
            ) : tab === 'Agent' ? (
              <div className="flex h-full min-h-0 flex-col gap-2">
                <UsageBar sessionId={current.session.id} model={run.model} />
                <div className="min-h-0 flex-1">
                  {agentView === 'terminal'
                    ? <Terminal sessionId={current.session.id} live={live && current.status === 'running'} artifact={terminalArtifact} />
                    : <StepsView sessionId={current.session.id} />}
                </div>
              </div>
            ) : tab === 'Events' ? (
              <EventsFeed sessionId={current.session.id} />
            ) : tab === 'Repository' ? (
              <RepositoryView runId={run.id} taskId={current.id} live={current.status === 'running'} />
            ) : tab === 'Output' ? (
              <OutputView artifacts={current.artifacts} stages={current.result?.details} />
            ) : tab === 'Retrieval' ? (
              <div className="flex h-full min-h-0 flex-col gap-2">
                <div className="flex shrink-0 flex-wrap gap-2 text-xs">
                  <ArtifactLink artifact={findArtifact(current.artifacts, 'retrieval-queries')}>Queries</ArtifactLink>
                  <ArtifactLink artifact={findArtifact(current.artifacts, 'retrieval-hits')}>Ranked hits</ArtifactLink>
                  <ArtifactLink artifact={findArtifact(current.artifacts, 'retrieval-provenance')}>Provenance</ArtifactLink>
                  <ArtifactLink artifact={findArtifact(current.artifacts, 'retrieval-invocations')}>Tool calls</ArtifactLink>
                </div>
                <pre className="min-h-0 flex-1 overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-canvas-inset p-3 text-xs text-fg-muted">
                  {loadingText ? 'Loading…' : text || emptyHint(tab, Boolean(current.result))}
                </pre>
              </div>
            ) : (
              <pre className="h-full min-h-0 overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-canvas-inset p-3 text-xs text-fg-muted">
                {loadingText ? 'Loading…' : text || emptyHint(tab, Boolean(current.result))}
              </pre>
            )}
          </div>
        </Card>

        {/* Results */}
        <Card className="flex min-h-0 flex-col">
          <div className="shrink-0 border-b border-border px-3 py-2 text-xs font-semibold text-fg">Results</div>
          <div className="min-h-0 flex-1 overflow-auto p-3">
            <Score run={run} />
            {current && (
              <div className="mt-4 space-y-3 text-xs">
                {current.result && (
                  <div className="space-y-1">
                    <Row k="Duration" v={formatDurationSeconds(current.result.durationSeconds)} />
                    <Row k="Tokens in/out" v={`${current.result.tokensInput.toLocaleString()} / ${current.result.tokensOutput.toLocaleString()}`} />
                    <Row k="Model" v={current.result.model} />
                    {contextNote(current.result) && <Row k="Context" v={contextNote(current.result)!} />}
                  </div>
                )}
                <ChecksPanel benchmarkKey={run.benchmark.key} task={current} />
                {current.result && <CostPanel result={current.result} />}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function ArtifactLink({ artifact, children }: { artifact?: ArtifactRef; children: React.ReactNode }) {
  if (!artifact) return null;
  return (
    <a href={artifact.viewUrl} target="_blank" rel="noreferrer"
      className="rounded-md border border-border px-2 py-1 text-accent-fg hover:bg-neutral-subtle">
      {children}
    </a>
  );
}

function ToggleBtn({ active, onClick, icon, children }: { active: boolean; onClick: () => void; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`flex items-center gap-1 rounded px-1.5 py-0.5 text-xs ${active ? 'bg-neutral-subtle text-fg' : 'text-fg-muted hover:text-fg'}`}>
      {icon}{children}
    </button>
  );
}

/** Context behaviour worth surfacing next to the numbers. */
function contextNote(result: any): string | null {
  const m = result?.metrics ?? {};
  const bits: string[] = [];
  if (m.contextTokens) bits.push(`${m.contextTokens.toLocaleString()} tokens used`);
  if (m.compactionCount) bits.push(`${m.compactionCount} compaction${m.compactionCount === 1 ? '' : 's'}`);
  if (m.contextOverflowCount) bits.push(`${m.contextOverflowCount} overflow${m.contextOverflowCount === 1 ? '' : 's'}`);
  return bits.length ? bits.join(' · ') : null;
}

/** Distinguish "nothing was produced" from "not produced yet". */
function emptyHint(tab: Tab, finished: boolean): string {
  if (!finished) return 'Not available until the task finishes.';
  return '(empty)';
}

/** Live score for the whole run.
 *  `passRate` is over *scored* tasks, so the bare "%" carries what it is a
 *  fraction of on hover: "100%" beside "1 / 3 passed" would otherwise read as a
 *  lie while a run is still going. The count of scored tasks is shown only while
 *  it differs from the total, and the rate is not repeated as a sentence. */
function Score({ run }: { run: any }) {
  const { passed, failed, timedOut, total } = run.counts;
  const scored = passed + failed + timedOut;
  const rate = Math.round((run.passRate ?? 0) * 100);
  return (
    <div className="space-y-2">
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold tabular-nums text-fg">{passed}</span>
        <span className="text-sm text-fg-muted">/ {total} passed</span>
        {scored > 0 && (
          <span className="ml-auto text-sm tabular-nums text-fg-muted"
            title={`pass rate over the ${scored} task${scored === 1 ? '' : 's'} scored${scored < total ? ' so far' : ''}`}>
            {rate}%
          </span>
        )}
      </div>
      <ProgressBar value={passed} total={total} state={run.status} />
      <div className="flex gap-3 text-xs text-fg-muted">
        <span><b className="text-success-fg">{passed}</b> passed</span>
        <span><b className="text-danger-fg">{failed}</b> failed</span>
        {timedOut > 0 && <span><b className="text-attention-fg">{timedOut}</b> timed out</span>}
        {scored < total && <span className="ml-auto">{scored}/{total} scored</span>}
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="shrink-0 text-fg-subtle">{k}</span>
      <span className="truncate text-fg">{v}</span>
    </div>
  );
}
