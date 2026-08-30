'use client';

import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Badge, Btn } from '@/components/ui';
import { withDashboardRow } from '@/lib/build';
import type { DashboardBuild, SystemReport, SystemRow } from '@/lib/build';
import type { ProviderInfo } from '@/lib/types';
import { Note, Panel } from './kit';

interface Credits {
  supported: boolean; detail?: string; label?: string;
  usage?: number; limit?: number | null; remaining?: number | null;
  exhausted?: boolean; freeTier?: boolean;
}

const usd = (n: number) => `$${n.toFixed(2)}`;


/** Credit balance for the BYOK key. An exhausted key makes every paid model 403,
 *  which looks exactly like an agent that refused to work — so it is worth a panel. */
function CreditsPanel() {
  const [c, setC] = useState<Credits | null>(null);
  const [busy, setBusy] = useState(false);

  const load = (refresh = false) => {
    setBusy(true);
    fetch(`/api/credits${refresh ? '?refresh=true' : ''}`).then((r) => r.json()).then(setC).finally(() => setBusy(false));
  };
  useEffect(() => { load(); }, []);

  const pct = c?.limit ? Math.min(100, ((c.usage ?? 0) / c.limit) * 100) : null;

  return (
    <Panel title="Provider credits" description="Reported by the provider for the configured key."
      actions={<Btn variant="invisible" loading={busy} icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={() => load(true)}>Refresh</Btn>}>
      {!c ? <Note>Loading…</Note> : !c.supported ? (
        <Note>{c.detail || 'This provider does not report credit balances.'}</Note>
      ) : (
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-fg-muted">Consumed</span>
            <span className="font-mono tabular-nums text-fg">
              {usd(c.usage ?? 0)}{c.limit != null && <span className="text-fg-subtle"> / {usd(c.limit)}</span>}
            </span>
          </div>
          {pct != null && (
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-muted">
              <div className={`h-full rounded-full ${c.exhausted ? 'bg-danger-fg' : pct > 80 ? 'bg-attention-fg' : 'bg-success-fg'}`}
                style={{ width: `${pct}%` }} />
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-fg-muted">Remaining</span>
            <span className={`font-mono tabular-nums ${c.exhausted ? 'text-danger-fg' : 'text-fg'}`}>
              {c.remaining != null ? usd(c.remaining) : 'no cap on this key'}
            </span>
          </div>
          {c.exhausted && (
            <Note>
              This key is spent. Paid models return <code>403 Key limit exceeded</code>; free models
              still run. A run that dies immediately with <code>provider_error</code> and no workspace
              change is this, not an agent failure.
            </Note>
          )}
          {c.freeTier && !c.exhausted && <Note>Free-tier key: paid models may be refused.</Note>}
        </div>
      )}
    </Panel>
  );
}

/** Model providers come from config.yaml, so this panel lists whatever the
 *  deployment declared rather than a vendor fixed in the dashboard. */
function ProvidersPanel({ providers }: { providers: ProviderInfo[] }) {
  if (!providers?.length) return null;
  return (
    <Panel title="Model providers" description="Declared in config.yaml. The active one serves every run.">
      <table className="w-full text-left text-xs">
        <tbody className="divide-y divide-border">
          {providers.map((p) => (
            <tr key={p.key}>
              <td className="py-1.5">
                <span className="text-fg">{p.name}</span>
                {p.active && <Badge variant="accent" className="ml-1.5">active</Badge>}
                <div className="font-mono text-[11px] text-fg-subtle">{p.baseUrl || 'no base URL'}</div>
              </td>
              <td className="py-1.5 text-right">
                <Badge variant={p.keyState === 'present' ? 'success' : p.keyState === 'absent' ? 'default' : 'default'}>
                  {p.keyState === 'not-required' ? 'no key needed' : `key ${p.keyState}`}
                </Badge>
                {p.apiKeyEnv && <div className="font-mono text-[11px] text-fg-subtle">{p.apiKeyEnv}</div>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

export function SystemRows({ rows }: { rows: SystemRow[] }) {
  return (
    <table className="w-full text-left text-xs">
      <tbody className="divide-y divide-border">
        {rows.map((r) => (
          <tr key={r.name}>
            <td className="w-40 py-1.5 align-top text-fg-muted">{r.name}</td>
            <td className="py-1.5">
              <span className={`font-mono text-xs ${r.state === 'absent' ? 'text-danger-fg' : 'text-fg'}`}>
                {r.value === 'absent' ? 'not installed' : r.value}
              </span>
              {(r.detail || r.neededBy) && (
                <div className="text-[11px] text-fg-subtle">{r.detail || `needed for ${r.neededBy}`}</div>
              )}
              {r.install && <div className="font-mono text-[11px] text-fg-subtle">{r.install}</div>}
            </td>
          </tr>
        ))}
        {rows.length === 0 && <tr><td className="py-1.5 text-fg-subtle">Nothing reported.</td></tr>}
      </tbody>
    </table>
  );
}

/**
 * What this deployment is, as opposed to what it has installed from plugins.
 *
 * Every command a plugin declares — agent CLIs, language servers — is reported
 * beside its plugin under Plugins, with the version that command answers with.
 * Repeating them here produced two lists of the same tools that disagreed.
 */
export function ServicesSection(
  { secrets, providers }: { secrets: Record<string, string>; providers: ProviderInfo[] },
) {
  const [sys, setSys] = useState<SystemReport | null>(null);
  const [build, setBuild] = useState<DashboardBuild | null>(null);
  const [busy, setBusy] = useState(false);

  const load = (refresh = false) => {
    setBusy(true);
    fetch(`/api/system${refresh ? '?refresh=true' : ''}`).then((r) => r.json()).then(setSys).finally(() => setBusy(false));
  };
  useEffect(() => { load(); }, []);
  // The dashboard's own build comes from the dashboard container, not the API.
  useEffect(() => {
    fetch('/rp-build').then((r) => (r.ok ? r.json() : null)).then(setBuild).catch(() => setBuild(null));
  }, []);

  return (
    <>
      <ProvidersPanel providers={providers} />

      <CreditsPanel />

      {/* Each row is a probe: `gradle --version` boots a JVM, and retrieval is
          asked over the network, so this can take seconds. The placeholder names
          what is being read rather than a panel that then never appears. */}
      {!sys
        ? <Panel title="Probing this deployment"><Note>Reading build identity, toolchain versions and retrieval status.</Note></Panel>
        : withDashboardRow(sys.groups, build).map((g) => (
          <Panel
            key={g.key}
            title={g.title}
            description={g.detail}
            actions={g.key === 'toolchain'
              ? <Btn variant="invisible" loading={busy} icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={() => load(true)}>Re-probe</Btn>
              : undefined}>
            <SystemRows rows={g.rows} />
          </Panel>
        ))}

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
