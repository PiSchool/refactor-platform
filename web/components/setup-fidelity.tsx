'use client';

import { AlertTriangle, CheckCircle2 } from 'lucide-react';

const MECHANISM: Record<string, { label: string; metric: string; noun: string }> = {
  s1_lsp: { label: 'Language server', metric: 'lspActions', noun: 'LSP action' },
  s3: { label: 'Native sub-agents', metric: 'subagentInvocations', noun: 'delegation' },
  s1_eval: { label: 'Self-check tool', metric: 'evalToolInvocations', noun: 'eval.sh run' },
  s2_rag_naive: { label: 'CPU code retrieval (naive)', metric: 'retrievalInvocations', noun: 'tool call' },
  s2_rag_ast: { label: 'CPU code retrieval (AST)', metric: 'retrievalInvocations', noun: 'tool call' },
};

/** Did this run actually use what its setup provides? Agent-driven mechanisms
 * require observed calls; S2 requires platform-driven context pre-injection. */
export function SetupFidelity({ setupKey, result }: { setupKey: string; result: any }) {
  const mech = MECHANISM[setupKey];
  if (!mech || !result) return null;

  const metrics = result.metrics ?? {};
  const count: number = metrics[mech.metric] ?? 0;
  const exercised: boolean | undefined = metrics.setupExercised;
  const s2 = setupKey.startsWith('s2_');
  const preInjected: boolean = metrics.retrievalPreInjected ?? false;
  if (exercised === undefined && !count && !preInjected) return null;   // pre-dates measurement

  const used = s2 ? preInjected && (exercised ?? true) : exercised ?? count > 0;

  return (
    <div className="rounded-md border border-border">
      <div className="flex items-center justify-between border-b border-border bg-canvas-subtle px-2 py-1.5">
        <span className="text-xs font-medium text-fg">Setup fidelity</span>
        <span className="font-mono text-[11px] text-fg-subtle">{setupKey}</span>
      </div>
      <div className="flex items-start gap-1.5 px-2 py-1.5">
        {used
          ? <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success-fg" />
          : <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-attention-fg" />}
        <div className="min-w-0 flex-1">
          <p className="text-xs text-fg">{mech.label}</p>
          <p className="break-words text-[11px] text-fg-subtle">
            {s2 && used
              ? `Context pre-injected on CPU; ${count} optional search-tool call${count === 1 ? '' : 's'}.`
              : s2
              ? 'Retrieval context was not injected, so this S2 task is not compliant.'
              : used
              ? `${count} ${mech.noun}${count === 1 ? '' : 's'} — the setup was exercised.`
              : `Never invoked. The agent was offered ${mech.label.toLowerCase()} and did not use it, so this run is mechanically a plain single-agent run.`}
          </p>
        </div>
      </div>
    </div>
  );
}
