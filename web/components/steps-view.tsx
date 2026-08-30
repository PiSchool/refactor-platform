'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { CheckCircle2, ChevronDown, ChevronRight, Loader2, XCircle } from 'lucide-react';
import type { AgentEvent } from '@/lib/events';
import { summarize, useSessionEvents } from '@/lib/events';

/** One collapsible group, mirroring a GitHub Actions step. */
interface Step {
  id: string;
  title: string;
  detail: string;
  status: 'ok' | 'failed' | 'running';
  startedAt?: string;
  endedAt?: string;
  lines: { at?: string; text: string; tone?: 'muted' | 'error' }[];
}

function ms(a?: string, b?: string): string {
  if (!a || !b) return '';
  const d = new Date(b).getTime() - new Date(a).getTime();
  if (!Number.isFinite(d) || d < 0) return '';
  return d < 1000 ? `${d}ms` : d < 60000 ? `${(d / 1000).toFixed(1)}s` : `${Math.floor(d / 60000)}m ${Math.round((d % 60000) / 1000)}s`;
}

/** A step is a summary of one turn. A reply of any size has to stay readable,
 *  and nothing is lost: the whole text is under Output, the raw session under
 *  Terminal. */
const MAX_LINES = 40;
const MAX_CHARS = 4000;

export function clipped(text: string): { text: string; omitted: string } {
  const lines = text.split('\n');
  let out = lines.slice(0, MAX_LINES).join('\n');
  if (out.length > MAX_CHARS) out = out.slice(0, MAX_CHARS);
  if (out.length >= text.length) return { text, omitted: '' };
  const hiddenLines = lines.length - out.split('\n').length;
  const what = hiddenLines > 0
    ? `${hiddenLines.toLocaleString('en-US')} more lines`
    : `${(text.length - out.length).toLocaleString('en-US')} more characters`;
  return { text: out, omitted: `[${what} — the full text is under Output]` };
}

/** Group the raw event stream into steps: session setup, then one group per
 *  assistant turn, with its tool calls as lines. */
export function toSteps(events: AgentEvent[]): Step[] {
  const steps: Step[] = [];
  const byTurn = new Map<string, Step>();
  let setup: Step | null = null;
  let turnOrdinal = 0;
  const pendingTools = new Map<string, { name: string; at?: string; step?: Step }>();

  for (const ev of events) {
    const d = ev.data ?? {};
    const type = ev.type;

    if (type.startsWith('session.') || type === 'system.message' || type === 'user.message') {
      if (!setup) {
        setup = { id: 'setup', title: 'Set up session', detail: '', status: 'ok', startedAt: ev.timestamp, lines: [] };
        steps.push(setup);
      }
      setup.endedAt = ev.timestamp;
      if (type === 'session.start') setup.detail = `${d.producer ?? 'agent'} · ${d.selectedModel ?? ''}`;
      if (type === 'session.shutdown') setup.detail ||= String(d.shutdownType ?? '');
      setup.lines.push({ at: ev.timestamp, text: `${type}  ${summarize(ev)}`, tone: 'muted' });
      continue;
    }

    if (type === 'assistant.turn_start') {
      // Copilot resets its raw turnId after some internal transitions (for
      // example before task_complete). UI identity must follow chronology,
      // otherwise duplicate React keys also couple both disclosure controls.
      const ordinal = turnOrdinal++;
      const step: Step = { id: `turn-${ordinal}`, title: `Turn ${ordinal}`, detail: '', status: 'running', startedAt: ev.timestamp, lines: [] };
      byTurn.set(String(d.turnId), step);
      steps.push(step);
      continue;
    }
    if (type === 'assistant.turn_end') {
      const step = byTurn.get(String(d.turnId));
      if (step) { step.status = 'ok'; step.endedAt = ev.timestamp; }
      continue;
    }

    const step = byTurn.get(String(d.turnId ?? ''));
    if (type === 'assistant.message') {
      const calls = (d.toolRequests ?? []).map((t: any) => t.name ?? t.function?.name).filter(Boolean);
      if (step) {
        if (d.content) {
          const { text, omitted } = clipped(String(d.content));
          step.lines.push({ at: ev.timestamp, text });
          if (omitted) step.lines.push({ text: omitted, tone: 'muted' });
        } else if (calls.length) step.lines.push({ at: ev.timestamp, text: `→ ${calls.join(', ')}`, tone: 'muted' });
        step.detail = calls.length ? calls.join(', ') : step.detail;
      }
      continue;
    }
    if (type === 'tool.execution_start') {
      pendingTools.set(String(d.toolCallId), { name: String(d.toolName ?? '?'), at: ev.timestamp, step });
      step?.lines.push({ at: ev.timestamp, text: `${d.toolName}(${JSON.stringify(d.arguments ?? {}).slice(0, 160)})`, tone: 'muted' });
      continue;
    }
    if (type === 'tool.execution_complete') {
      const started = pendingTools.get(String(d.toolCallId));
      pendingTools.delete(String(d.toolCallId));
      const target = started?.step ?? step;
      const ok = d.success !== false;
      const out = String(d.result?.content ?? '').trim();
      target?.lines.push({
        at: ev.timestamp,
        text: `${started?.name ?? 'tool'} → ${ok ? 'ok' : 'failed'}${ms(started?.at, ev.timestamp) ? ` (${ms(started?.at, ev.timestamp)})` : ''}${out ? `\n${out.slice(0, 600)}` : ''}`,
        tone: ok ? undefined : 'error',
      });
      if (!ok && target) target.status = 'failed';
      continue;
    }
    if (type.startsWith('hook.')) continue; // noise
  }
  return steps;
}

export function StepsView({ sessionId }: { sessionId: string }) {
  const events = useSessionEvents(sessionId);
  const steps = useMemo(() => toSteps(events), [events]);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const boxRef = useRef<HTMLDivElement>(null);
  const autoScroll = useRef(true);

  useEffect(() => {
    const el = boxRef.current;
    if (el && autoScroll.current) el.scrollTop = el.scrollHeight;
  }, [steps.length]);

  if (!events.length) return <p className="p-3 text-xs text-fg-subtle">Waiting for the agent…</p>;

  return (
    <div
      ref={boxRef}
      onScroll={(e) => {
        const el = e.currentTarget;
        autoScroll.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
      }}
      className="h-full min-h-0 overflow-auto rounded-md border border-border bg-canvas-inset">
      {steps.map((s) => {
        const isOpen = open[s.id] ?? s.status === 'failed';
        return (
          <div key={s.id} className="border-b border-border last:border-0">
            <button onClick={() => setOpen((o) => ({ ...o, [s.id]: !isOpen }))}
              className="flex w-full items-center gap-2 px-2 py-1.5 text-left hover:bg-neutral-subtle">
              {isOpen ? <ChevronDown className="h-3.5 w-3.5 shrink-0 text-fg-muted" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0 text-fg-muted" />}
              {s.status === 'ok' ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success-fg" />
                : s.status === 'failed' ? <XCircle className="h-3.5 w-3.5 shrink-0 text-danger-fg" />
                : <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-attention-fg" />}
              <span className="shrink-0 text-xs font-medium text-fg">{s.title}</span>
              <span className="truncate font-mono text-[11px] text-fg-subtle">{s.detail}</span>
              <span className="ml-auto shrink-0 font-mono text-[11px] tabular-nums text-fg-subtle">{ms(s.startedAt, s.endedAt)}</span>
            </button>
            {isOpen && (
              <div className="bg-canvas px-2 py-1">
                {s.lines.map((l, i) => (
                  <div key={i} className="flex gap-2 py-px font-mono text-xs leading-5">
                    <span className="w-16 shrink-0 select-none text-right text-fg-subtle">
                      {l.at ? new Date(l.at).toISOString().slice(11, 19) : ''}
                    </span>
                    <span className={`whitespace-pre-wrap break-all ${l.tone === 'error' ? 'text-danger-fg' : l.tone === 'muted' ? 'text-fg-muted' : 'text-fg'}`}>
                      {l.text}
                    </span>
                  </div>
                ))}
                {s.lines.length === 0 && <p className="py-1 text-xs text-fg-subtle">No output.</p>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
