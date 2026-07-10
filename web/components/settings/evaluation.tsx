'use client';

import { useEffect, useState } from 'react';
import { RotateCcw, Save } from 'lucide-react';
import { Badge, Btn } from '@/components/ui';
import { getJson, Note, Panel } from './kit';

interface Stage { preset: string; config: Record<string, unknown>; enabled: boolean }
interface EvalDoc {
  benchmark: string;
  capture: string[];
  overridden: boolean;
  corePresets: string[];
  pluginStages: string[];
  shipped: { verify: { preset: string; config: any }[]; passed: string };
  effective: { verify: Stage[]; passed: string };
}

export function EvaluationSection({ benchmark }: { benchmark: string }) {
  const [doc, setDoc] = useState<EvalDoc | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [passed, setPassed] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  // guard against a stale response from a previously-selected benchmark
  useEffect(() => {
    let stale = false;
    setDoc(null); setMsg('');
    getJson<EvalDoc>(`/api/benchmarks/${benchmark}/evaluation`).then((d) => {
      if (stale || !d) return;
      setDoc(d); setStages(d.effective.verify); setPassed(d.effective.passed);
    });
    return () => { stale = true; };
  }, [benchmark]);

  if (!doc) return <Panel title="Evaluation & metrics"><Note>Loading…</Note></Panel>;

  async function save() {
    setBusy(true); setMsg('');
    const res = await fetch(`/api/benchmarks/${benchmark}/evaluation`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ verify: stages, passed }),
    });
    setBusy(false);
    if (!res.ok) { setMsg(`Failed: ${(await res.json().catch(() => ({}))).detail ?? res.status}`); return; }
    const d: EvalDoc = await res.json();
    setDoc(d); setStages(d.effective.verify); setPassed(d.effective.passed);
    setMsg('Saved — applies to the next run.');
  }

  async function reset() {
    setBusy(true);
    const res = await fetch(`/api/benchmarks/${benchmark}/evaluation`, { method: 'DELETE' });
    setBusy(false);
    if (!res.ok) return;
    const d: EvalDoc = await res.json();
    setDoc(d); setStages(d.effective.verify); setPassed(d.effective.passed);
    setMsg('Reset to the values the plugin ships.');
  }

  const patch = (i: number, next: Partial<Stage>) =>
    setStages((s) => s.map((st, j) => (j === i ? { ...st, ...next } : st)));

  return (
    <>
      <Panel
        title="Verify pipeline"
        description="Gating stages, in order. Edits are overrides — the plugin's manifest still decides which stages exist."
        actions={
          <>
            <Btn variant="primary" loading={busy} icon={<Save className="h-3.5 w-3.5" />} onClick={save}>Save</Btn>
            <Btn variant="outline" disabled={!doc.overridden || busy} icon={<RotateCcw className="h-3.5 w-3.5" />} onClick={reset}>Reset</Btn>
            {doc.overridden && <Badge variant="attention">overridden</Badge>}
          </>
        }>
        <div className="space-y-3">
          {stages.map((s, i) => (
            <div key={s.preset} className="rounded-md border border-border">
              <div className="flex items-center gap-2 border-b border-border bg-canvas-subtle px-2 py-1.5">
                <input type="checkbox" checked={s.enabled} onChange={(e) => patch(i, { enabled: e.target.checked })} />
                <span className="font-mono text-xs text-fg">{s.preset}</span>
                <span className="ml-auto text-[10px] text-fg-subtle">
                  {s.preset.includes('.') ? 'plugin stage' : 'core preset'}
                </span>
              </div>
              <StageConfig value={s.config} onChange={(config) => patch(i, { config })} />
            </div>
          ))}
          {stages.length === 0 && <Note>This benchmark defines no gating stages.</Note>}
        </div>

        <div className="mt-4">
          <label className="text-xs text-fg">Pass expression</label>
          <p className="text-[11px] text-fg-subtle">Boolean over stage names, e.g. <code className="font-mono">workspace_changed and python_tests</code></p>
          <input value={passed} onChange={(e) => setPassed(e.target.value)}
            className="mt-1 h-8 w-full rounded-md border border-border bg-canvas-inset px-2 font-mono text-xs text-fg" />
        </div>

        {msg && <p className="mt-2"><Note tone={msg.startsWith('Failed') ? 'error' : 'ok'}>{msg}</Note></p>}
      </Panel>

      <Panel title="Captured metrics" description="Non-gating stages that record artifacts and metrics.">
        <div className="flex flex-wrap gap-1.5">
          {doc.capture.map((c) => (
            <span key={c} className="rounded-full border border-border px-2 py-0.5 font-mono text-[11px] text-fg-muted">{c}</span>
          ))}
          {doc.capture.length === 0 && <Note>None.</Note>}
        </div>
        <p className="mt-3 text-[11px] text-fg-subtle">
          Available core presets: <span className="font-mono">{doc.corePresets.join(', ')}</span>
          {doc.pluginStages.length > 0 && <> · plugin stages: <span className="font-mono">{doc.pluginStages.join(', ')}</span></>}
        </p>
      </Panel>
    </>
  );
}

/** Stage config is free-form JSON in the manifest; edit it as key/value rows. */
function StageConfig({ value, onChange }: { value: Record<string, unknown>; onChange: (v: Record<string, unknown>) => void }) {
  const entries = Object.entries(value ?? {});
  if (entries.length === 0) return <p className="px-2 py-1.5 text-[11px] text-fg-subtle">No options.</p>;
  return (
    <div className="divide-y divide-border">
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-center gap-2 px-2 py-1.5">
          <span className="w-44 shrink-0 font-mono text-[11px] text-fg-muted">{k}</span>
          <input
            value={typeof v === 'object' ? JSON.stringify(v) : String(v)}
            onChange={(e) => {
              const raw = e.target.value;
              const next = /^-?\d+$/.test(raw) ? Number(raw) : raw === 'true' ? true : raw === 'false' ? false : raw;
              onChange({ ...value, [k]: next });
            }}
            className="h-7 flex-1 rounded border border-border bg-canvas-inset px-2 font-mono text-[11px] text-fg" />
        </div>
      ))}
    </div>
  );
}
