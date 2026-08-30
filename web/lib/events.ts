/**
 * @module events
 * @description The agent's native events.jsonl: streaming hook + one-line
 * summaries. Shared by the raw Events tab and the grouped Steps view.
 */
'use client';

import { useEffect, useState } from 'react';

export interface AgentEvent {
  type: string;
  id?: string;
  timestamp?: string;
  data?: Record<string, any>;
}

/** Replays the whole file, then tails it while the session runs.
 *
 *  On a dropped connection we reconnect and replay from the start rather than
 *  giving up: a feed that dies on the first hiccup shows an empty Events tab for
 *  the rest of a run. The server always replays the whole file, so resetting
 *  state on reconnect is what keeps events from being duplicated. */
export function useSessionEvents(sessionId: string): AgentEvent[] {
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    if (!sessionId) return;
    let es: EventSource | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let closed = false;

    const connect = () => {
      setEvents([]); // the server replays from the top; start clean
      es = new EventSource(`/api/sessions/${sessionId}/events`);
      es.addEventListener('event', (e: MessageEvent) => {
        try {
          const ev = JSON.parse(e.data) as AgentEvent;
          setEvents((prev) => (prev.length > 8000 ? [...prev.slice(-6000), ev] : [...prev, ev]));
        } catch {
          /* a malformed line must not kill the feed */
        }
      });
      // The server sends `end` when the session is over. Anything else that closes
      // the stream is a dropped connection, and is worth retrying.
      es.addEventListener('end', () => { closed = true; es?.close(); });
      es.onerror = () => {
        es?.close();
        if (!closed) retry = setTimeout(connect, 2000);
      };
    };

    connect();
    return () => { closed = true; clearTimeout(retry); es?.close(); };
  }, [sessionId]);

  return events;
}

function clip(v: unknown, n = 140) {
  const s = typeof v === 'string' ? v : JSON.stringify(v ?? '');
  return s.length > n ? `${s.slice(0, n)}…` : s;
}

/** A one-line human summary per event type; unknown types fall back to JSON. */
export function summarize(ev: AgentEvent): string {
  const d = ev.data ?? {};
  switch (ev.type) {
    case 'session.start': {
      // Every adapter reports `version`; `copilotVersion` is what Copilot's own
      // stream calls it. Reading only the vendor key labelled every other tool
      // `v?`, and an unknown version is left out rather than shown as one.
      const version = d.version ?? d.copilotVersion;
      return `${d.producer ?? 'agent'}${version ? ` v${version}` : ''} · model ${d.selectedModel ?? '?'}`;
    }
    case 'session.model_change':
      return d.previousModel === d.newModel ? `model ${d.newModel}` : `model ${d.previousModel} → ${d.newModel}`;
    case 'session.mode_changed':
      return `mode ${d.previousMode} → ${d.newMode}`;
    case 'session.permissions_changed':
      return `allow-all permissions: ${d.previousAllowAllPermissions} → ${d.allowAllPermissions}`;
    case 'session.shutdown': {
      const m = d.modelMetrics ?? {};
      const usage = Object.values(m)[0] as any;
      const tin = usage?.usage?.inputTokens ?? usage?.inputTokens;
      const tout = usage?.usage?.outputTokens ?? usage?.outputTokens;
      return `${d.shutdownType ?? 'shutdown'}${tin != null ? ` · ${tin}/${tout} tokens` : ''}`;
    }
    case 'user.message':
    case 'system.message':
      return clip(d.content);
    case 'assistant.message': {
      const calls = (d.toolRequests ?? []).map((t: any) => t.name ?? t.function?.name).filter(Boolean);
      if (d.content) return clip(d.content);
      return calls.length ? `→ ${calls.join(', ')}` : '(no content)';
    }
    case 'assistant.turn_start':
    case 'assistant.turn_end':
      return `turn ${d.turnId}`;
    case 'tool.execution_start':
      return `${d.toolName ?? '?'}(${clip(d.arguments, 90)})`;
    case 'tool.execution_complete':
      return `${d.success === false ? 'failed' : 'ok'}${d.result?.content ? ` · ${clip(d.result.content, 90)}` : ''}`;
    case 'hook.start':
    case 'hook.end':
      return `${d.hookType ?? ''}${d.success === false ? ' · failed' : ''}`;
    default:
      return clip(d, 120);
  }
}

export interface LiveUsage {
  /** exact, live: summed from assistant.message.outputTokens */
  outputTokens: number;
  /** exact, live: one per successful session.compaction_complete */
  compactions: number;
  /** exact, live: assistant.message count */
  turns: number;
  /** the agent reports these only in session.shutdown; null until then */
  final: FinalUsage | null;
}

export interface FinalUsage {
  inputTokens: number;
  cacheReadTokens: number;
  reasoningTokens: number;
  /** context occupancy at the end of the session */
  contextTokens: number;
}

/** Roll the event stream into usage.
 *
 *  The agent emits `outputTokens` per assistant message, and nothing else about
 *  tokens until `session.shutdown` — which is where `inputTokens`, cache and
 *  reasoning splits, and `currentTokens` (true context occupancy) first appear.
 *  There is no live prompt-side signal to derive them from, so `final` stays
 *  null and callers show nothing rather than a guess. */
export function liveUsage(events: AgentEvent[]): LiveUsage {
  const usage: LiveUsage = { outputTokens: 0, compactions: 0, turns: 0, final: null };

  for (const ev of events) {
    const d = ev.data ?? {};
    switch (ev.type) {
      case 'assistant.message':
        usage.outputTokens += Number(d.outputTokens ?? 0);
        usage.turns += 1;
        break;
      case 'session.compaction_complete':
        if (d.success !== false) usage.compactions += 1;
        break;
      case 'session.shutdown': {
        const final: FinalUsage = { inputTokens: 0, cacheReadTokens: 0, reasoningTokens: 0, contextTokens: 0 };
        for (const m of Object.values((d.modelMetrics ?? {}) as Record<string, any>)) {
          final.inputTokens += Number(m?.usage?.inputTokens ?? 0);
          final.cacheReadTokens += Number(m?.usage?.cacheReadTokens ?? 0);
          final.reasoningTokens += Number(m?.usage?.reasoningTokens ?? 0);
        }
        final.contextTokens = Number(d.currentTokens ?? 0);
        usage.final = final;
        break;
      }
    }
  }
  return usage;
}

export function eventTone(type: string): string {
  const family = type.split('.')[0];
  return ({
    session: 'text-accent-fg',
    assistant: 'text-done-fg',
    tool: 'text-attention-fg',
    user: 'text-fg',
    system: 'text-fg-muted',
    hook: 'text-fg-subtle',
  } as Record<string, string>)[family] ?? 'text-fg-muted';
}
