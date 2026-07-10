'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Download, FileSpreadsheet, ListTree, RotateCcw, SkipForward, Square, Terminal as TerminalIcon, Trash2,
} from 'lucide-react';
import { useRun, useRunAction } from '@/lib/api';
import { Btn, Card, Elapsed, ProgressBar, StatusBadge, StatusIcon, SkeletonCard } from '@/components/ui';
import { Terminal } from '@/components/terminal';
import { EventsFeed } from '@/components/events-feed';
import { StepsView } from '@/components/steps-view';
import { RepositoryView } from '@/components/repository-view';
import { OutputView } from '@/components/output-view';
import { ChecksPanel } from '@/components/checks-panel';
import { UsageBar } from '@/components/usage-bar';
import { CostPanel } from '@/components/cost-panel';
import { formatDurationSeconds, runOutcome } from '@/lib/utils';

const TABS = ['Agent', 'Repository', 'Output', 'Prompt', 'Events'] as const;
type Tab = (typeof TABS)[number];

/** Which artifact backs each text tab. Repository/Output are served live. */
const ARTIFACT: Partial<Record<Tab, 'prompt'>> = { Prompt: 'prompt' };

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: run, isLoading } = useRun(id);
  const { stop, restart, del, skip } = useRunAction();
  const [selected, setSelected] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('Agent');
  const [agentView, setAgentView] = useState<'steps' | 'terminal'>('steps');
  const [text, setText] = useState('');
  const [loadingText, setLoadingText] = useState(false);

  const tasks = run?.tasks || [];
  const current = tasks.find((t) => t.id === selected) || tasks[0];
  const live = ['running', 'queued'].includes(run?.status || '');
  const s3 = run?.setup.key === 's3';

  useEffect(() => { if (!selected && tasks[0]) setSelected(tasks[0].id); }, [tasks, selected]);

  useEffect(() => {
    const key = ARTIFACT[tab];
    setText('');
    if (!key || !current) return;
    const path = current.artifacts?.[key] ?? current.result?.artifacts[key];
    if (!path) return;
    let stale = false;
    setLoadingText(true);
    fetch(`/api/artifact?path=${encodeURIComponent(path)}`)
      .then((r) => (r.ok ? r.text() : r.status === 404 ? '' : `(unavailable: HTTP ${r.status})`))
      .then((t) => { if (!stale) setText(t); })
      .catch((e) => { if (!stale) setText(`(failed to load: ${e})`); })
      .finally(() => { if (!stale) setLoadingText(false); });
    return () => { stale = true; };
  }, [tab, current]);

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
          <div className="flex items-center gap-1.5">
            <a href={`/api/runs/${run.id}/export.csv`}><Btn variant="outline" icon={<FileSpreadsheet className="h-3.5 w-3.5" />}>CSV</Btn></a>
            <a href={`/api/runs/${run.id}/export`}><Btn variant="outline" icon={<Download className="h-3.5 w-3.5" />}>Export ZIP</Btn></a>
            {!live && <Btn variant="outline" icon={<RotateCcw className="h-3.5 w-3.5" />} onClick={() => restart.mutate(run.id)}>Restart</Btn>}
            {live && <Btn variant="danger" icon={<Square className="h-3.5 w-3.5" />} onClick={() => stop.mutate(run.id)}>Stop</Btn>}
            {!live && <Btn variant="invisible" icon={<Trash2 className="h-3.5 w-3.5" />} onClick={() => del.mutate(run.id)}>Delete</Btn>}
          </div>
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
                  <p className="text-[10px] text-fg-subtle">
                    {t.result
                      ? `${formatDurationSeconds(t.result.durationSeconds)} · ${t.result.tokensInput + t.result.tokensOutput} tok`
                      : t.status === 'running'
                      ? <>running · <Elapsed startedAt={t.startedAt} finishedAt={t.finishedAt} /></>
                      : t.status}
                  </p>
                </div>
                {live && current?.id === t.id && t.status === 'running' && (
                  <span onClick={(e) => { e.stopPropagation(); skip.mutate({ runId: run.id, taskId: t.id }); }} title="Skip">
                    <SkipForward className="h-3.5 w-3.5 text-fg-muted hover:text-fg" />
                  </span>
                )}
              </button>
            ))}
          </div>
        </Card>

        {/* Session viewer */}
        <Card className="flex min-h-0 flex-col">
          <div className="flex shrink-0 items-center gap-1 border-b border-border px-2 py-1.5">
            {TABS.map((t) => (
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
                    ? <Terminal sessionId={current.session.id} live={live && current.status === 'running'} />
                    : <StepsView sessionId={current.session.id} />}
                </div>
              </div>
            ) : tab === 'Events' ? (
              <EventsFeed sessionId={current.session.id} />
            ) : tab === 'Repository' ? (
              <RepositoryView runId={run.id} taskId={current.id} live={current.status === 'running'} />
            ) : tab === 'Output' ? (
              <OutputView runId={run.id} taskId={current.id} stages={current.result?.details} />
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

function ToggleBtn({ active, onClick, icon, children }: { active: boolean; onClick: () => void; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] ${active ? 'bg-neutral-subtle text-fg' : 'text-fg-muted hover:text-fg'}`}>
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

/** Live score for the whole run: the progress bar belongs with the numbers.
 *  `passRate` is over *scored* tasks, so it must not be shown as a bare "%" —
 *  "100%" next to "1 / 3 passed" reads as a lie while a run is still going. */
function Score({ run }: { run: any }) {
  const { passed, failed, timedOut, total } = run.counts;
  const scored = passed + failed + timedOut;
  const rate = Math.round((run.passRate ?? 0) * 100);
  return (
    <div className="space-y-2">
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold tabular-nums text-fg">{passed}</span>
        <span className="text-sm text-fg-muted">/ {total} passed</span>
      </div>
      <ProgressBar value={passed} total={total} state={run.status} />
      <div className="flex gap-3 text-[11px] text-fg-muted">
        <span><b className="text-success-fg">{passed}</b> passed</span>
        <span><b className="text-danger-fg">{failed}</b> failed</span>
        {timedOut > 0 && <span><b className="text-attention-fg">{timedOut}</b> timed out</span>}
        <span className="ml-auto">{scored}/{total} scored</span>
      </div>
      {scored > 0 && (
        <p className="text-[11px] text-fg-subtle">
          <span className="tabular-nums text-fg">{rate}%</span> pass rate over {scored} scored{scored < total ? ' so far' : ''}
        </p>
      )}
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
