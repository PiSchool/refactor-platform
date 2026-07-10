'use client';

import { useEffect, useState } from 'react';
import { RotateCcw, Save } from 'lucide-react';
import { Badge, Btn } from '@/components/ui';
import type { PromptDoc, PromptInfo } from '@/lib/types';
import { getJson, Note, Panel } from './kit';

/** The list is tagged with the benchmark it describes, so a selection left over
 *  from the previous benchmark can never be fetched (that 404'd and, before the
 *  null-guard, crashed the page on `text.trim()`). */
interface Listing { benchmark: string; prompts: PromptInfo[] }

export function PromptsSection({ benchmark }: { benchmark: string }) {
  const [list, setList] = useState<Listing | null>(null);
  const [name, setName] = useState('');
  const [doc, setDoc] = useState<PromptDoc | null>(null);
  const [text, setText] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let stale = false;
    setList(null); setName(''); setDoc(null); setText(''); setMsg('');
    getJson<{ prompts: PromptInfo[] }>(`/api/prompts/${benchmark}`).then((d) => {
      if (!stale) setList({ benchmark, prompts: d?.prompts ?? [] });
    });
    return () => { stale = true; };
  }, [benchmark]);

  const ready = list?.benchmark === benchmark;

  useEffect(() => {
    if (!ready || !name || !list!.prompts.some((p) => p.name === name)) { setDoc(null); setText(''); return; }
    let stale = false;
    getJson<PromptDoc>(`/api/prompts/${benchmark}/${name}`).then((d) => {
      if (stale) return;
      if (!d) { setDoc(null); setText(''); setMsg('Template not found for this benchmark.'); return; }
      setDoc(d); setText(d.content ?? ''); setMsg('');
    });
    return () => { stale = true; };
  }, [benchmark, name, ready, list]);

  async function save() {
    setBusy(true);
    const res = await fetch(`/api/prompts/${benchmark}/${name}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: text }),
    });
    setBusy(false);
    setMsg(res.ok ? 'Saved — applies to the next run.' : `Failed: HTTP ${res.status}`);
    if (res.ok) {
      setDoc((d) => (d ? { ...d, overridden: true } : d));
      setList((l) => (l ? { ...l, prompts: l.prompts.map((p) => (p.name === name ? { ...p, overridden: true } : p)) } : l));
    }
  }

  async function reset() {
    setBusy(true);
    await fetch(`/api/prompts/${benchmark}/${name}`, { method: 'DELETE' });
    const d = await getJson<PromptDoc>(`/api/prompts/${benchmark}/${name}`);
    setBusy(false);
    if (d) { setDoc(d); setText(d.content ?? ''); }
    setMsg('Reset to the template the plugin ships.');
    setList((l) => (l ? { ...l, prompts: l.prompts.map((p) => (p.name === name ? { ...p, overridden: false } : p)) } : l));
  }

  return (
    <Panel title="Prompt templates" description="Edits are stored outside the image and take precedence over the plugin's default."
      actions={doc && (
        <>
          <Btn variant="primary" loading={busy} disabled={!text.trim()} icon={<Save className="h-3.5 w-3.5" />} onClick={save}>Save</Btn>
          <Btn variant="outline" loading={busy} disabled={!doc.overridden} icon={<RotateCcw className="h-3.5 w-3.5" />} onClick={reset}>Reset</Btn>
          {doc.overridden && <Badge variant="attention">overridden</Badge>}
        </>
      )}>
      {!ready ? <Note>Loading…</Note> : (
        <>
          <select value={name} onChange={(e) => setName(e.target.value)}
            className="h-8 w-full rounded-md border border-border bg-canvas-inset px-2 text-xs text-fg">
            <option value="">Select a template…</option>
            {list!.prompts.map((p) => <option key={p.name} value={p.name}>{p.name}{p.overridden ? ' (edited)' : ''}</option>)}
          </select>
          {list!.prompts.length === 0 && <p className="mt-2"><Note>This benchmark ships no editable templates.</Note></p>}

          {doc && (
            <textarea value={text} onChange={(e) => setText(e.target.value)} spellCheck={false} rows={18}
              className="mt-3 w-full rounded-md border border-border bg-canvas-inset p-2 font-mono text-[11px] leading-5 text-fg" />
          )}
          {msg && <p className="mt-2"><Note tone={msg.startsWith('Failed') || msg.includes('not found') ? 'error' : 'ok'}>{msg}</Note></p>}
        </>
      )}
    </Panel>
  );
}
