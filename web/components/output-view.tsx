'use client';

import { useEffect, useMemo, useState } from 'react';
import { StatusIcon } from '@/components/ui';
import { fetchArtifactText } from '@/lib/api';
import { isProblem, stripAnsi, tone } from '@/lib/log';
import type { ArtifactRef } from '@/lib/types';

interface EvidenceEntry extends ArtifactRef { label: string; stage?: string }

/** The engine writes `<stage>.log` with dots replaced by underscores. */
const fileStem = (stage: string) => stage.replace(/\./g, '_');

function evidenceEntry(artifact: ArtifactRef): EvidenceEntry | null {
  if (!artifact.available) return null;
  if (artifact.key.startsWith('eval-log:')) {
    const stage = artifact.key.slice('eval-log:'.length);
    return { ...artifact, label: stage, stage };
  }
  if (artifact.key === 'self-check-limit') {
    return { ...artifact, label: 'self-check limit' };
  }
  if (artifact.key.startsWith('self-check:')) {
    return { ...artifact, label: artifact.key.replaceAll(':', ' ') };
  }
  return null;
}

export function OutputView({ artifacts, stages }: {
  artifacts?: ArtifactRef[]; stages?: Record<string, unknown>;
}) {
  const entries = useMemo(
    () => (artifacts ?? []).map(evidenceEntry).filter((entry): entry is EvidenceEntry => entry !== null),
    [artifacts],
  );
  const entryKeys = entries.map((entry) => entry.key).join('\u0000');
  const [active, setActive] = useState(() => entries[0]?.key ?? '');
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [onlyProblems, setOnlyProblems] = useState(false);

  useEffect(() => {
    setActive((current) => entries.some((item) => item.key === current) ? current : entries[0]?.key ?? '');
    setText('');
  }, [entryKeys]);

  const entry = entries.find((item) => item.key === active);

  useEffect(() => {
    if (!entry) { setText(''); return; }
    let stale = false;
    setLoading(true);
    fetchArtifactText(entry)
      .then((t) => { if (!stale) setText(stripAnsi(t)); })
      .catch((error) => { if (!stale) setText(`(unavailable: ${error})`); })
      .finally(() => { if (!stale) setLoading(false); });
    return () => { stale = true; };
  }, [entry?.viewUrl]);

  const lines = useMemo(() => {
    const all = text.split('\n');
    if (!onlyProblems) return all;
    return all.filter(isProblem);
  }, [text, onlyProblems]);

  if (entries.length === 0) {
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
        {entries.map((item) => {
          const ok = item.stage ? statusOf(item.stage) : undefined;
          return (
            <button key={item.key} onClick={() => setActive(item.key)}
              className={`flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs ${
                active === item.key ? 'border-accent-fg bg-accent-subtle/30 text-fg' : 'border-border text-fg-muted hover:text-fg'}`}>
              {ok !== undefined && <StatusIcon status={ok ? 'passed' : 'failed'} className="h-3 w-3" />}
              <span className="font-mono">{item.label}</span>
              <span className="text-[11px] text-fg-subtle">{(item.sizeBytes / 1024).toFixed(1)}kB</span>
            </button>
          );
        })}
        <label className="ml-auto flex items-center gap-1 text-xs text-fg-muted">
          <input type="checkbox" checked={onlyProblems} onChange={(e) => setOnlyProblems(e.target.checked)} />
          errors &amp; warnings only
        </label>
        {entry && (
          <a href={entry.downloadUrl} target="_blank" rel="noreferrer"
            className="text-xs text-accent-fg hover:underline">download</a>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-border bg-canvas-inset">
        {loading ? <p className="p-3 text-xs text-fg-subtle">Loading…</p> : (
          <table className="w-full border-collapse font-mono text-xs leading-5">
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
