'use client';

/**
 * The prompt a benchmark sends to the agent.
 *
 * A template was chosen from a dropdown whose entries carried their own scope,
 * name and edited-state concatenated into one line, and the values the benchmark
 * substitutes were explained in a paragraph above the text. Here the templates
 * are a list that shows which one is selected and which have been edited, and
 * each value is a marker that says whether the text still contains it and puts
 * it at the caret when clicked. A template missing a required value cannot be
 * saved, which is the same rule the server applies.
 */

import { useEffect, useRef, useState } from 'react';
import {
  CircleAlert, CircleCheck, FileCode2, Minus, RotateCcw, Save, Target,
} from 'lucide-react';
import { Chip, Dot, IconBtn } from '@/components/controls';
import { Btn } from '@/components/ui';
import { insertToken, missingRequired, syntaxGlyph, syntaxTitle, variableRows } from '@/lib/prompts';
import type { VariableRow } from '@/lib/prompts';
import type { PromptDoc, PromptInfo } from '@/lib/types';
import { getJson, Note, Panel } from './kit';

const ICON = 'h-3.5 w-3.5 shrink-0';

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
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState(false);
  const editor = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    let stale = false;
    setList(null); setName(''); setDoc(null); setText(''); setMsg(''); setFailed(false);
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
      if (!d) { setDoc(null); setText(''); setFailed(true); setMsg('This benchmark has no template by that name.'); return; }
      setDoc(d); setText(d.content ?? ''); setMsg(''); setFailed(false);
    });
    return () => { stale = true; };
  }, [benchmark, name, ready, list]);

  const rows = doc ? variableRows(text, doc.syntax, doc.variables) : [];
  const missing = missingRequired(rows);
  const dirty = Boolean(doc) && text !== (doc!.content ?? '');

  async function save() {
    setBusy(true); setFailed(false);
    const res = await fetch(`/api/prompts/${benchmark}/${name}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: text }),
    });
    setBusy(false);
    if (!res.ok) {
      setFailed(true);
      setMsg((await res.json().catch(() => ({}))).detail ?? `HTTP ${res.status}`);
      return;
    }
    setMsg('Saved. The next run uses it.');
    setDoc((d) => (d ? { ...d, content: text, overridden: true } : d));
    setList((l) => (l ? { ...l, prompts: l.prompts.map((p) => (p.name === name ? { ...p, overridden: true } : p)) } : l));
  }

  async function reset() {
    setBusy(true); setFailed(false);
    await fetch(`/api/prompts/${benchmark}/${name}`, { method: 'DELETE' });
    const d = await getJson<PromptDoc>(`/api/prompts/${benchmark}/${name}`);
    setBusy(false);
    if (d) { setDoc(d); setText(d.content ?? ''); }
    setMsg('Restored to the template the plugin ships.');
    setList((l) => (l ? { ...l, prompts: l.prompts.map((p) => (p.name === name ? { ...p, overridden: false } : p)) } : l));
  }

  /** Put a value where the caret is, so a template is repaired without typing
   *  the bracket form from memory. */
  function insert(placeholder: string) {
    const area = editor.current;
    const at = area?.selectionStart ?? text.length;
    const to = area?.selectionEnd ?? at;
    const { text: next, caret } = insertToken(text, at, to, placeholder);
    setText(next);
    if (area) {
      requestAnimationFrame(() => { area.focus(); area.setSelectionRange(caret, caret); });
    }
  }

  return (
    <Panel
      title="Prompt templates"
      description="The benchmark selects a template per task and substitutes its values. An edit is stored outside the image and takes precedence over the plugin's own."
      actions={doc && (
        <>
          {dirty && <Dot label="unsaved changes" />}
          {doc.overridden && <Chip tone="attention" title="Edited here; the plugin's own template is one click away">edited</Chip>}
          <Btn variant="primary" loading={busy} disabled={!dirty || !text.trim() || missing.length > 0}
            icon={<Save className={ICON} />} onClick={save}>Save</Btn>
          <IconBtn icon={<RotateCcw className={ICON} />} label="Restore the template the plugin ships"
            disabled={!doc.overridden || busy} onClick={reset} />
        </>
      )}>
      {!ready ? <Note>Loading…</Note> : list!.prompts.length === 0 ? (
        <Note>This benchmark ships no editable template.</Note>
      ) : (
        <div className="grid gap-3 lg:grid-cols-[14rem_1fr]">
          <TemplateList prompts={list!.prompts} selected={name} onSelect={setName} />

          <div className="min-w-0">
            {!doc ? (
              <Note>Select a template.</Note>
            ) : (
              <>
                <div className="flex flex-wrap items-center gap-1.5">
                  {syntaxGlyph(doc.syntax) && (
                    <Chip mono title={syntaxTitle(doc.syntax)}>{syntaxGlyph(doc.syntax)}</Chip>
                  )}
                  {doc.appliesTo && (
                    <Chip icon={<Target className="h-3 w-3" />} title={`Used for ${doc.appliesTo}`}>{doc.appliesTo}</Chip>
                  )}
                  {rows.length === 0 && <Note>This benchmark declares no substituted value for this template.</Note>}
                  {rows.map((row) => (
                    <VariableChip key={row.name} row={row} onInsert={insert} />
                  ))}
                </div>

                <textarea
                  ref={editor}
                  aria-label={`${doc.name} template`}
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  spellCheck={false}
                  rows={18}
                  className="mt-2 w-full rounded-md border border-border bg-canvas-inset p-2 font-mono text-[11px] leading-5 text-fg outline-none focus:border-accent-fg" />

                {missing.length > 0 && (
                  <p className="mt-1.5 flex items-center gap-1.5">
                    <CircleAlert className={`${ICON} text-danger-fg`} aria-hidden="true" />
                    <Note tone="error">{`Save is blocked: the template no longer contains ${missing.join(', ')}.`}</Note>
                  </p>
                )}
                {msg && (
                  <p className="mt-1.5 flex items-center gap-1.5">
                    {failed
                      ? <CircleAlert className={`${ICON} text-danger-fg`} aria-hidden="true" />
                      : <CircleCheck className={`${ICON} text-success-fg`} aria-hidden="true" />}
                    <Note tone={failed ? 'error' : 'ok'}>{msg}</Note>
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </Panel>
  );
}

export function TemplateList({ prompts, selected, onSelect }: {
  prompts: PromptInfo[];
  selected: string;
  onSelect: (name: string) => void;
}) {
  return (
    <ul className="max-h-80 divide-y divide-border overflow-auto rounded-md border border-border">
      {prompts.map((prompt) => {
        const active = prompt.name === selected;
        return (
          <li key={prompt.name}>
            <button
              type="button"
              aria-current={active}
              onClick={() => onSelect(prompt.name)}
              title={prompt.appliesTo ? `${prompt.name} — used for ${prompt.appliesTo}` : prompt.name}
              className={`flex w-full items-center gap-1.5 px-2 py-1.5 text-left transition-colors ${
                active ? 'bg-sidenav-selected' : 'hover:bg-neutral-subtle'}`}>
              <FileCode2 className={`h-3.5 w-3.5 shrink-0 ${active ? 'text-fg' : 'text-fg-subtle'}`} aria-hidden="true" />
              <span className={`min-w-0 flex-1 truncate font-mono text-[11px] ${active ? 'text-fg' : 'text-fg-muted'}`}>
                {prompt.name}
              </span>
              {prompt.overridden && <Dot label="edited here" />}
            </button>
          </li>
        );
      })}
    </ul>
  );
}

const VARIABLE = {
  present: { tone: 'success', Icon: CircleCheck, note: 'in the template' },
  missing: { tone: 'danger', Icon: CircleAlert, note: 'required, and no longer in the template' },
  unused: { tone: 'neutral', Icon: Minus, note: 'optional, not used by this template' },
} as const;

/** A value the benchmark substitutes, and whether the text still uses it. */
export function VariableChip({ row, onInsert }: { row: VariableRow; onInsert?: (placeholder: string) => void }) {
  const { tone, Icon, note } = VARIABLE[row.state];
  const title = `${row.placeholder} — ${row.summary || row.name}: ${note}`;
  const body = (
    <Chip icon={<Icon className="h-3 w-3" />} tone={tone} mono title={title}>{row.name}</Chip>
  );
  if (!onInsert || row.state === 'present') return body;
  return (
    <button type="button" onClick={() => onInsert(row.placeholder)} title={`${title}. Click to insert it.`}
      className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-fg">
      {body}
    </button>
  );
}
