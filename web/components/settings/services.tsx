'use client';

import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Badge, Btn, StatusIcon } from '@/components/ui';
import { Note, Panel } from './kit';

export function ServicesSection({ secrets, lsp }: { secrets: Record<string, string>; lsp: any[] }) {
  const [sys, setSys] = useState<Record<string, string> | null>(null);
  const [busy, setBusy] = useState(false);

  const load = (refresh = false) => {
    setBusy(true);
    fetch(`/api/system${refresh ? '?refresh=true' : ''}`).then((r) => r.json()).then(setSys).finally(() => setBusy(false));
  };
  useEffect(() => { load(); }, []);

  return (
    <>
      <Panel title="Toolchain" description="Probed inside the backend container; results are cached."
        actions={<Btn variant="invisible" loading={busy} icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={() => load(true)}>Refresh</Btn>}>
        {!sys ? <Note>Loading…</Note> : (
          <table className="w-full text-left text-xs">
            <tbody className="divide-y divide-border">
              {Object.entries(sys).map(([k, v]) => (
                <tr key={k}>
                  <td className="w-32 py-1.5 text-fg-muted">{k}</td>
                  <td className={`py-1.5 font-mono text-[11px] ${v === 'absent' ? 'text-danger-fg' : 'text-fg'}`}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>

      <Panel title="Language servers" description="Used by the S1-LSP setup.">
        {lsp.map((l) => (
          <div key={l.key} className="flex items-center gap-1.5 py-0.5 text-xs">
            <StatusIcon status={l.available ? 'passed' : 'failed'} className="h-3.5 w-3.5" />
            <span className="text-fg">{l.key}</span>
            <span className="text-fg-subtle">({l.language})</span>
          </div>
        ))}
      </Panel>

      <Panel title="Credentials" description="Stored Secrets">
        {Object.entries(secrets).map(([k, v]) => (
          <div key={k} className="flex items-center justify-between py-0.5 text-xs">
            <span className="text-fg-muted">{k}</span>
            <Badge variant={v === 'present' ? 'success' : 'default'}>{String(v)}</Badge>
          </div>
        ))}
      </Panel>
    </>
  );
}
