'use client';

import { Fragment, useMemo, useState } from 'react';
import { ChevronDown, ChevronRight, FileDiff } from 'lucide-react';
import { parseDiff, diffTotals, type DiffFile } from '@/lib/diff';

const STATUS_LABEL: Record<DiffFile['status'], string> = {
  added: 'added', deleted: 'deleted', renamed: 'renamed', modified: 'modified',
};

export function DiffView({ text }: { text: string }) {
  const files = useMemo(() => parseDiff(text), [text]);
  const totals = useMemo(() => diffTotals(files), [files]);

  if (!files.length) {
    return <p className="p-3 text-xs text-fg-subtle">The agent made no changes to the repository.</p>;
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 items-center gap-2 border-b border-border px-2 pb-2 text-xs text-fg-muted">
        <FileDiff className="h-3.5 w-3.5" />
        <span>{files.length} changed {files.length === 1 ? 'file' : 'files'}</span>
        <span className="text-success-fg">+{totals.additions}</span>
        <span className="text-danger-fg">−{totals.deletions}</span>
      </div>
      <div className="min-h-0 flex-1 space-y-2 overflow-auto p-2">
        {files.map((f) => <DiffFileBlock key={f.path} file={f} />)}
      </div>
    </div>
  );
}

export function DiffFileBlock({ file }: { file: DiffFile }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <button onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 bg-canvas-subtle px-2 py-1.5 text-left hover:bg-neutral-subtle">
        {open ? <ChevronDown className="h-3.5 w-3.5 shrink-0 text-fg-muted" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0 text-fg-muted" />}
        <span className="truncate font-mono text-xs text-fg">{file.path}</span>
        {file.status !== 'modified' && (
          <span className="shrink-0 rounded-full border border-border px-1.5 text-[11px] text-fg-muted">{STATUS_LABEL[file.status]}</span>
        )}
        <span className="ml-auto shrink-0 space-x-1.5 font-mono text-xs">
          <span className="text-success-fg">+{file.additions}</span>
          <span className="text-danger-fg">−{file.deletions}</span>
        </span>
      </button>

      {open && (file.binary ? (
        <p className="px-3 py-2 text-xs text-fg-subtle">Binary file not shown.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse font-mono text-xs leading-5">
            <tbody>
              {file.hunks.map((h, hi) => (
                <Fragment key={`h${hi}`}>
                  <tr>
                    <td colSpan={3} className="bg-accent-subtle/30 px-2 py-0.5 text-accent-fg">{h.header}</td>
                  </tr>
                  {h.lines.map((l, li) => (
                    <tr key={`h${hi}l${li}`} className={
                      l.kind === 'add' ? 'bg-success-subtle/40'
                        : l.kind === 'del' ? 'bg-danger-subtle/40'
                        : l.kind === 'meta' ? 'bg-canvas-subtle' : ''}>
                      <td className="w-10 select-none border-r border-border px-1 text-right align-top text-fg-subtle">{l.oldNo ?? ''}</td>
                      <td className="w-10 select-none border-r border-border px-1 text-right align-top text-fg-subtle">{l.newNo ?? ''}</td>
                      <td className={`whitespace-pre-wrap break-all px-2 ${
                        l.kind === 'add' ? 'text-success-fg' : l.kind === 'del' ? 'text-danger-fg' : 'text-fg'}`}>
                        <span className="select-none text-fg-subtle">{l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' '}</span>
                        {l.text}
                      </td>
                    </tr>
                  ))}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
