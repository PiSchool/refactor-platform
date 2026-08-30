'use client';

import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import { Badge, Btn } from '@/components/ui';
import type { BenchmarkPlugin } from '@/lib/types';
import { Panel } from './kit';

export function BenchmarksSection({ benchmarks, onChanged }: {
  benchmarks: BenchmarkPlugin[];
  onChanged: () => void | Promise<unknown>;
}) {
  const [busy, setBusy] = useState('');
  const [actionError, setActionError] = useState('');

  useEffect(() => {
    const sources = benchmarks
      .filter((benchmark) => benchmark.dataState === 'provisioning')
      .map((benchmark) => {
        const source = new EventSource(`/api/benchmarks/${benchmark.key}/bootstrap/events`);
        source.addEventListener('status', (event) => {
          const update = JSON.parse((event as MessageEvent<string>).data) as { dataState: string };
          if (update.dataState !== 'provisioning') {
            source.close();
            void onChanged();
          }
        });
        return source;
      });
    return () => sources.forEach((source) => source.close());
  }, [benchmarks, onChanged]);

  async function bootstrap(key: string) {
    setBusy(key);
    setActionError('');
    try {
      const response = await fetch(`/api/benchmarks/${key}/bootstrap`, { method: 'POST' });
      if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
      await onChanged();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Benchmark provisioning request failed.');
    } finally {
      setBusy('');
    }
  }

  return (
    <Panel title="Benchmarks" description="Discovered from plugins/. Data is provisioned ahead of runs — never fetched at task time.">
      <table className="w-full text-left text-xs">
        <thead className="text-[11px] uppercase tracking-wide text-fg-subtle">
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
                <div className="font-mono text-[11px] text-fg-subtle">{b.key}</div>
              </td>
              <td className="py-2 text-fg-muted">{b.language}</td>
              <td className="py-2 tabular-nums text-fg-muted">{b.taskCount.toLocaleString()}</td>
              <td className="py-2 font-mono text-[11px] text-fg-subtle">{b.setups.join(', ')}</td>
              <td className="py-2">
                <Badge variant={b.dataState === 'ready' ? 'success' : b.dataState === 'error' ? 'danger' : 'attention'}>
                  {b.dataState}
                </Badge>
                {b.dataState === 'error' && b.dataError && (
                  <div className="mt-1 max-w-72 break-words text-[11px] text-danger-fg" title={b.dataError}>
                    {b.dataError}
                  </div>
                )}
              </td>
              <td className="py-2 text-right">
                {b.dataState !== 'ready' && (
                  <Btn variant="outline" loading={busy === b.key || b.dataState === 'provisioning'}
                    disabled={b.dataState === 'provisioning'} icon={<Download className="h-3.5 w-3.5" />}
                    onClick={() => bootstrap(b.key)}>
                    {b.dataState === 'error' ? 'Retry' : b.dataState === 'provisioning' ? 'Provisioning' : 'Bootstrap'}
                  </Btn>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {actionError && <p className="mt-3 text-xs text-danger-fg">{actionError}</p>}
    </Panel>
  );
}
