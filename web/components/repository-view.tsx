'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ChevronDown, ChevronRight, FileText, Folder, FolderOpen, GitBranch,
  GitCommitHorizontal, RefreshCw,
} from 'lucide-react';
import { parseDiff, diffTotals, type DiffFile } from '@/lib/diff';
import { DiffFileBlock } from '@/components/diff-view';

type Change = { status: string; path: string };
type Entry = { name: string; path: string; dir: boolean; sizeBytes: number };
type Repo = {
  source?: string; ref?: string; baseline?: string; workspacePath?: string;
  live?: boolean; changedFiles?: Change[]; error?: string;
};

const STATUS: Record<string, { label: string; cls: string }> = {
  M: { label: 'M', cls: 'text-attention-fg' },
  A: { label: 'A', cls: 'text-success-fg' },
  D: { label: 'D', cls: 'text-danger-fg' },
  R: { label: 'R', cls: 'text-done-fg' },
  '??': { label: 'U', cls: 'text-fg-muted' },
};
const badge = (code: string) => STATUS[code] ?? STATUS[code[0]] ?? { label: code, cls: 'text-fg-muted' };

const POLL_MS = 3000;

/** Repository: the exact checkout the agent is working in — its changes as a
 *  diff, and the whole tree for navigation. Polls while the task is running. */
export function RepositoryView({ runId, taskId, live }: { runId: string; taskId: string; live: boolean }) {
  const [repo, setRepo] = useState<Repo | null>(null);
  const [diffText, setDiffText] = useState('');
  const [mode, setMode] = useState<'changes' | 'files'>('changes');
  const [selected, setSelected] = useState<string | null>(null);
  const [fileText, setFileText] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setRefreshing(true);
    const [r, d] = await Promise.all([
      fetch(`/api/runs/${runId}/tasks/${taskId}/repo`).then((x) => (x.ok ? x.json() : null)).catch(() => null),
      fetch(`/api/runs/${runId}/tasks/${taskId}/diff`).then((x) => (x.ok ? x.json() : null)).catch(() => null),
    ]);
    setRepo(r);
    setDiffText(d?.diff ?? '');
    setRefreshing(false);
  }, [runId, taskId]);

  useEffect(() => {
    setSelected(null); setFileText(''); setDiffText(''); setRepo(null);
    load();
  }, [runId, taskId, load]);

  // The diff must track the workspace, exactly like the file list does.
  useEffect(() => {
    if (!live) return;
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [live, load]);

  const files = useMemo(() => parseDiff(diffText), [diffText]);
  const totals = useMemo(() => diffTotals(files), [files]);
  const changed = repo?.changedFiles ?? [];
  const changedByPath = useMemo(
    () => Object.fromEntries(changed.map((c) => [c.path, c.status])), [changed]);

  useEffect(() => {
    if (!selected) { setFileText(''); return; }
    let stale = false;
    fetch(`/api/runs/${runId}/tasks/${taskId}/file?path=${encodeURIComponent(selected)}`)
      .then((r) => (r.ok ? r.text() : `(unavailable: HTTP ${r.status})`))
      .then((t) => { if (!stale) setFileText(t); })
      .catch(() => {});
    return () => { stale = true; };
  }, [runId, taskId, selected]);

  if (!repo) return <p className="p-3 text-xs text-fg-subtle">Loading repository…</p>;

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      {/* branch bar */}
      <div className="shrink-0 rounded-md border border-border bg-canvas-subtle px-3 py-2">
        <div className="flex items-center gap-2 text-xs">
          <GitBranch className="h-3.5 w-3.5 shrink-0 text-fg-muted" />
          <span className="truncate font-mono text-fg">{repo.source ?? '—'}</span>
          {live && <span className="shrink-0 rounded-full bg-success-subtle px-1.5 text-[10px] text-success-fg">live</span>}
          <button onClick={load} title="Refresh" className="ml-auto shrink-0 text-fg-muted hover:text-fg">
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <div className="mt-1 flex items-center gap-2 text-[11px] text-fg-muted">
          <GitCommitHorizontal className="h-3.5 w-3.5 shrink-0" />
          <span className="font-mono">{(repo.baseline ?? repo.ref ?? '—').slice(0, 12)}</span>
          <span className="text-fg-subtle">baseline</span>
          <span className="ml-auto space-x-1.5 font-mono">
            <span className="text-success-fg">+{totals.additions}</span>
            <span className="text-danger-fg">−{totals.deletions}</span>
            <span className="text-fg-subtle">{changed.length} changed</span>
          </span>
        </div>
      </div>

      <div className="flex shrink-0 gap-0.5 rounded-md border border-border p-0.5 text-xs">
        <Seg active={mode === 'changes'} onClick={() => setMode('changes')}>Changes ({changed.length})</Seg>
        <Seg active={mode === 'files'} onClick={() => setMode('files')}>All files</Seg>
      </div>

      {repo.error && <p className="shrink-0 text-xs text-danger-fg">{repo.error}</p>}

      {mode === 'changes' ? (
        <div className="min-h-0 flex-1 overflow-auto">
          {files.length === 0 ? (
            <p className="p-3 text-xs text-fg-subtle">
              {live ? 'No changes yet — the agent has not edited any files.' : 'The agent made no changes to the repository.'}
            </p>
          ) : (
            <div className="space-y-2">{files.map((f: DiffFile) => <DiffFileBlock key={f.path} file={f} />)}</div>
          )}
        </div>
      ) : (
        <div className="grid min-h-0 flex-1 grid-cols-[260px_1fr] gap-2">
          <div className="min-h-0 overflow-auto rounded-md border border-border">
            <Tree runId={runId} taskId={taskId} path="" depth={0}
              changed={changedByPath} selected={selected} onSelect={setSelected} />
          </div>
          <div className="min-h-0 overflow-auto rounded-md border border-border bg-canvas-inset">
            {!selected ? (
              <p className="p-3 text-xs text-fg-subtle">Select a file to view its contents.</p>
            ) : (
              <>
                <div className="sticky top-0 flex items-center gap-2 border-b border-border bg-canvas-subtle px-3 py-1.5">
                  <span className="truncate font-mono text-[11px] text-fg">{selected}</span>
                  {changedByPath[selected] && (
                    <span className={`ml-auto shrink-0 font-mono text-[10px] ${badge(changedByPath[selected]).cls}`}>
                      {badge(changedByPath[selected]).label}
                    </span>
                  )}
                </div>
                <table className="w-full border-collapse font-mono text-[11px] leading-5">
                  <tbody>
                    {fileText.split('\n').map((l, i) => (
                      <tr key={i}>
                        <td className="w-12 select-none border-r border-border px-1 text-right align-top text-fg-subtle">{i + 1}</td>
                        <td className="whitespace-pre-wrap break-all px-2 text-fg">{l || ' '}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Seg({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`rounded px-2 py-1 ${active ? 'bg-neutral-subtle text-fg' : 'text-fg-muted hover:text-fg'}`}>
      {children}
    </button>
  );
}

/** Lazy directory tree: each level is fetched when it is first expanded. */
function Tree({ runId, taskId, path, depth, changed, selected, onSelect }: {
  runId: string; taskId: string; path: string; depth: number;
  changed: Record<string, string>; selected: string | null; onSelect: (p: string) => void;
}) {
  const [entries, setEntries] = useState<Entry[] | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});

  useEffect(() => {
    let stale = false;
    fetch(`/api/runs/${runId}/tasks/${taskId}/tree?path=${encodeURIComponent(path)}`)
      .then((r) => (r.ok ? r.json() : { entries: [] }))
      .then((d) => { if (!stale) setEntries(d.entries ?? []); })
      .catch(() => { if (!stale) setEntries([]); });
    return () => { stale = true; };
  }, [runId, taskId, path]);

  if (!entries) return <p className="px-2 py-1 text-[11px] text-fg-subtle">…</p>;
  if (entries.length === 0 && depth === 0) {
    return <p className="p-3 text-xs text-fg-subtle">Workspace not available (it was cleaned up after the run).</p>;
  }

  return (
    <ul>
      {entries.map((e) => {
        const isOpen = open[e.path];
        const mark = changed[e.path];
        return (
          <li key={e.path}>
            <button
              onClick={() => (e.dir ? setOpen((o) => ({ ...o, [e.path]: !isOpen })) : onSelect(e.path))}
              style={{ paddingLeft: 6 + depth * 12 }}
              className={`flex w-full items-center gap-1 py-0.5 pr-2 text-left text-[11px] hover:bg-neutral-subtle ${
                selected === e.path ? 'bg-neutral-subtle' : ''}`}>
              {e.dir ? (
                <>
                  {isOpen ? <ChevronDown className="h-3 w-3 shrink-0 text-fg-subtle" /> : <ChevronRight className="h-3 w-3 shrink-0 text-fg-subtle" />}
                  {isOpen ? <FolderOpen className="h-3.5 w-3.5 shrink-0 text-accent-fg" /> : <Folder className="h-3.5 w-3.5 shrink-0 text-accent-fg" />}
                </>
              ) : (
                <>
                  <span className="w-3 shrink-0" />
                  <FileText className="h-3.5 w-3.5 shrink-0 text-fg-subtle" />
                </>
              )}
              <span className={`truncate font-mono ${mark ? 'text-fg' : 'text-fg-muted'}`}>{e.name}</span>
              {mark && <span className={`ml-auto shrink-0 font-mono text-[10px] ${badge(mark).cls}`}>{badge(mark).label}</span>}
            </button>
            {e.dir && isOpen && (
              <Tree runId={runId} taskId={taskId} path={e.path} depth={depth + 1}
                changed={changed} selected={selected} onSelect={onSelect} />
            )}
          </li>
        );
      })}
    </ul>
  );
}
