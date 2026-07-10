'use client';

import { useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import { Btn } from '@/components/ui';
import { useModels } from '@/lib/api';
import { Field, Input, Note, Panel } from './kit';
import { ModelPicker } from './model-picker';

export function RunDefaults({ editable, onSaved }: { editable: any; onSaved: () => void }) {
  const [form, setForm] = useState(editable);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const { data: models } = useModels();

  useEffect(() => setForm(editable), [editable]);

  const set = (k: string) => (e: any) =>
    setForm((f: any) => ({ ...f, [k]: typeof f[k] === 'number' ? Number(e.target.value) : e.target.value }));

  async function save() {
    setSaving(true); setMsg('');
    const res = await fetch('/api/settings', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form),
    });
    setSaving(false);
    setMsg(res.ok ? 'Saved.' : `Failed: HTTP ${res.status}`);
    if (res.ok) onSaved();
  }

  return (
    <Panel title="Run defaults" description="Applied to new runs; each run keeps the values it was created with."
      actions={<><Btn variant="primary" loading={saving} icon={<Save className="h-3.5 w-3.5" />} onClick={save}>Save</Btn>{msg && <Note>{msg}</Note>}</>}>
      <div className="divide-y divide-border">
        <Field label="Default model" hint={models?.source === 'provider' || models?.source === 'cache'
          ? `${models.models.length} models offered by the provider`
          : 'Provider catalog unavailable — type any model id'}>
          <ModelPicker value={form.activeModel} onChange={(id) => setForm((f: any) => ({ ...f, activeModel: id }))} />
        </Field>
        <Field label="Cost-projection model"
          hint="Runs show what the same tokens would have cost on this model. Leave empty to disable.">
          <ModelPicker value={form.costModel ?? ''} allowEmpty
            onChange={(id) => setForm((f: any) => ({ ...f, costModel: id }))} />
        </Field>
        <Field label="Default task timeout" hint="Seconds before the agent process is killed">
          <Input type="number" value={form.defaultTaskTimeout} onChange={set('defaultTaskTimeout')} className="w-32" />
        </Field>
        <Field label="Retention cap" hint="How many runs to keep on disk">
          <Input type="number" value={form.retentionCap} onChange={set('retentionCap')} className="w-32" />
        </Field>
        <Field label="Eval-tool max attempts" hint="S1-eval: how often the agent may self-check">
          <Input type="number" value={form.evalToolMaxAttempts} onChange={set('evalToolMaxAttempts')} className="w-32" />
        </Field>
        <Field label="Keep task workspaces" hint="Needed to browse a finished task's repository; costs disk (a guava checkout is hundreds of MB)">
          <input type="checkbox" checked={!!form.keepWorkspace}
            onChange={(e) => setForm((f: any) => ({ ...f, keepWorkspace: e.target.checked }))} />
        </Field>
      </div>
    </Panel>
  );
}
