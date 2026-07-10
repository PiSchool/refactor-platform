'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';
import { Badge, Btn } from '@/components/ui';
import { Panel } from './kit';

export function BenchmarksSection({ benchmarks, onChanged }: { benchmarks: any[]; onChanged: () => void }) {
  const [busy, setBusy] = useState('');

  async function bootstrap(key: string) {
    setBusy(key);
    await fetch(`/api/benchmarks/${key}/bootstrap`, { method: 'POST' });
    setTimeout(() => { setBusy(''); onChanged(); }, 1500);
  }

  return (
    <Panel title="Benchmarks" description="Discovered from plugins/. Data is provisioned ahead of runs — never fetched at task time.">
      <table className="w-full text-left text-xs">
        <thead className="text-[10px] uppercase tracking-wide text-fg-subtle">
          <tr className="border-b border-border">
            <th className="pb-1.5 font-medium">Name</th>
            <th className="pb-1.5 font-medium">Lang</th>
            <th className="pb-1.5 font-medium">Tasks</th>
            <th className="pb-1.5 font-medium">Setups</th>
            <th className="pb-1.5 font-medium">Data</th>
            <th />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {benchmarks.map((b) => (
            <tr key={b.key}>
              <td className="py-2">
                <span className="text-fg">{b.name}</span>
                <span className="ml-1.5 font-mono text-[10px] text-fg-subtle">v{b.version}</span>
                <div className="font-mono text-[10px] text-fg-subtle">{b.key}</div>
              </td>
              <td className="py-2 text-fg-muted">{b.language}</td>
              <td className="py-2 tabular-nums text-fg-muted">{b.taskCount}</td>
              <td className="py-2 font-mono text-[10px] text-fg-subtle">{b.setups.join(', ')}</td>
              <td className="py-2">
                <Badge variant={b.dataState === 'ready' ? 'success' : b.dataState === 'error' ? 'danger' : 'attention'}>
                  {b.dataState}
                </Badge>
              </td>
              <td className="py-2 text-right">
                {b.dataState !== 'ready' && (
                  <Btn variant="outline" loading={busy === b.key} icon={<Download className="h-3.5 w-3.5" />}
                    onClick={() => bootstrap(b.key)}>Bootstrap</Btn>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}
