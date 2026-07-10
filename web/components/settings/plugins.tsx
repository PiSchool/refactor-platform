'use client';

import { Panel, Note } from './kit';

export function PluginsSection({ plugins, errors }: { plugins: any; errors: string[] }) {
  return (
    <>
      {errors?.length > 0 && (
        <Panel title="Plugin errors" description="These plugins failed to load and were skipped.">
          {errors.map((e) => <p key={e} className="font-mono text-[11px] text-danger-fg">{e}</p>)}
        </Panel>
      )}

      <Panel title="Agent tools" description="AI CLI tools discovered from plugins/agents.">
        <table className="w-full text-left text-xs">
          <tbody className="divide-y divide-border">
            {plugins.agents.map((a: any) => (
              <tr key={a.key}>
                <td className="py-2 text-fg">{a.name} <span className="font-mono text-[10px] text-fg-subtle">v{a.version}</span></td>
                <td className="py-2 text-right font-mono text-[10px] text-fg-muted">
                  {Object.entries(a.capabilities).filter(([, v]) => v).map(([k]) => k).join(' · ') || 'no capabilities'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <Panel title="Setups" description="Platform-owned execution profiles. Plugins declare compatibility; they never define setups.">
        <table className="w-full text-left text-xs">
          <tbody className="divide-y divide-border">
            {plugins.setups.map((s: any) => (
              <tr key={s.key}>
                <td className="w-40 py-2 text-fg">{s.name}<div className="font-mono text-[10px] text-fg-subtle">{s.key}</div></td>
                <td className="py-2 text-fg-muted">{s.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </>
  );
}
