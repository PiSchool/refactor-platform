'use client';

import { type ReactNode, useEffect, useState } from 'react';
import { CircleAlert, CircleCheck, Save } from 'lucide-react';
import { Btn } from '@/components/ui';
import { Dot, Switch } from '@/components/controls';
import { useModels } from '@/lib/api';
import { Field, Input, Note, Panel } from './kit';
import { ModelPicker } from './model-picker';

/** A number field with its unit inside it, rather than spelled out again in the
 *  hint beside it. */
function WithUnit({ children, unit }: { children: ReactNode; unit: string }) {
  return (
    <span className="relative inline-flex items-center">
      {children}
      <span className="pointer-events-none absolute right-2 text-[11px] text-fg-subtle">{unit}</span>
    </span>
  );
}

export function RunDefaults({ editable, onSaved }: {
  editable: any;
  onSaved: () => void;
}) {
  const [form, setForm] = useState(editable);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const [failed, setFailed] = useState(false);
  const { data: models } = useModels();

  useEffect(() => setForm(editable), [editable]);

  const set = (k: string) => (e: any) =>
    setForm((f: any) => ({ ...f, [k]: typeof f[k] === 'number' ? Number(e.target.value) : e.target.value }));

  const dirty = JSON.stringify(form) !== JSON.stringify(editable);

  async function save() {
    setSaving(true); setMsg('');
    try {
      const res = await fetch('/api/settings', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form),
      });
      setFailed(!res.ok);
      setMsg(res.ok ? 'Saved.' : `HTTP ${res.status}`);
      if (res.ok) onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <Panel title="Run defaults" description="Applied to new runs; each run keeps the values it was created with."
      actions={(
        <>
          {dirty && <Dot label="unsaved changes" />}
          <Btn variant="primary" loading={saving} disabled={!dirty} icon={<Save className="h-3.5 w-3.5" />} onClick={save}>Save</Btn>
          {msg && (
            <span className="flex items-center gap-1">
              {failed
                ? <CircleAlert className="h-3.5 w-3.5 shrink-0 text-danger-fg" aria-hidden="true" />
                : <CircleCheck className="h-3.5 w-3.5 shrink-0 text-success-fg" aria-hidden="true" />}
              <Note tone={failed ? 'error' : 'ok'}>{msg}</Note>
            </span>
          )}
        </>
      )}>
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
        <Field label="Task timeout" hint="The agent process is killed after this long on one task.">
          <WithUnit unit="s">
            <Input type="number" value={form.defaultTaskTimeout} onChange={set('defaultTaskTimeout')} className="w-32 pr-7" />
          </WithUnit>
        </Field>
        <Field label="Runs kept on disk" hint="The oldest run beyond this count is pruned. An imported study archive is never pruned.">
          <Input type="number" value={form.retentionCap} onChange={set('retentionCap')} className="w-32" />
        </Field>
        <Field label="Self-check attempts" hint="How often an agent may run the evaluation tool on its own work, in the setups that offer it.">
          <Input type="number" value={form.evalToolMaxAttempts} onChange={set('evalToolMaxAttempts')} className="w-32" />
        </Field>
        <Field label="Keep task workspaces" hint="Required to browse a finished task's repository afterwards. A checkout can be hundreds of megabytes.">
          <Switch checked={!!form.keepWorkspace} label="Keep task workspaces"
            onChange={(keepWorkspace) => setForm((f: any) => ({ ...f, keepWorkspace }))} />
        </Field>
      </div>
    </Panel>
  );
}
