'use client';

import { useEffect, useState } from 'react';
import { Download, RefreshCw } from 'lucide-react';
import { Badge, Btn } from '@/components/ui';
import { getJson, Note, Panel } from './kit';

interface Repo { type: string; source: string; taskCount: number; mirrorPath: string; present: boolean; sizeBytes: number }

function size(n: number) {
  if (!n) return '—';
  const u = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
}

export function ReposSection({ benchmark }: { benchmark: string }) {
  const [repos, setRepos] = useState<Repo[] | null>(null);
  const [busy, setBusy] = useState('');

  const load = () => getJson<{ repos: Repo[] }>(`/api/benchmarks/${benchmark}/repos`).then((d) => setRepos(d?.repos ?? []));

  useEffect(() => {
    let stale = false;
    setRepos(null);
    getJson<{ repos: Repo[] }>(`/api/benchmarks/${benchmark}/repos`).then((d) => { if (!stale) setRepos(d?.repos ?? []); });
    return () => { stale = true; };
  }, [benchmark]);

  async function mirror(source: string) {
    setBusy(source);
    await fetch(`/api/benchmarks/${benchmark}/repos/mirror`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source }),
    });
    setTimeout(() => { setBusy(''); load(); }, 2500);
  }

  return (
    <Panel title="Repositories" description="Workspace sources these tasks check out. Mirrors are cloned once, so no network is touched at task time."
      actions={<Btn variant="invisible" icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={load}>Refresh</Btn>}>
      {!repos ? <Note>Loading…</Note> : repos.length === 0 ? <Note>No sources.</Note> : (
        <table className="w-full text-left text-xs">
          <thead className="text-[10px] uppercase tracking-wide text-fg-subtle">
            <tr className="border-b border-border">
              <th className="pb-1.5 font-medium">Source</th>
              <th className="pb-1.5 font-medium">Type</th>
              <th className="pb-1.5 font-medium">Tasks</th>
              <th className="pb-1.5 font-medium">Size</th>
              <th className="pb-1.5 font-medium">State</th>
              <th />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {repos.map((r) => (
              <tr key={r.source}>
                <td className="max-w-[22rem] truncate py-2 font-mono text-[11px] text-fg">{r.source}</td>
                <td className="py-2 text-fg-muted">{r.type}</td>
                <td className="py-2 tabular-nums text-fg-muted">{r.taskCount}</td>
                <td className="py-2 tabular-nums text-fg-muted">{size(r.sizeBytes)}</td>
                <td className="py-2">
                  <Badge variant={r.present ? 'success' : 'attention'}>{r.present ? 'present' : 'missing'}</Badge>
                </td>
                <td className="py-2 text-right">
                  {r.type === 'git' && (
                    <Btn variant="outline" loading={busy === r.source} icon={<Download className="h-3.5 w-3.5" />}
                      onClick={() => mirror(r.source)}>{r.present ? 'Re-clone' : 'Clone'}</Btn>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  );
}
