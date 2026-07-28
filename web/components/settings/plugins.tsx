'use client';

/**
 * The inventory: what is installed under `plugins/`, in one place.
 *
 * Four groups, one row each: name, id, what it provides, and whether it can run
 * here — with the command that installs it when it cannot. Nothing is configured
 * on this screen. A benchmark's data is fetched on the Benchmarks screen, a
 * metric is tuned on the Evaluation screen, and neither is repeated here.
 *
 * A row states the version its command reports, never a number written in a
 * manifest: the two disagreed, and the manifest's was the one a finished run
 * recorded.
 */

import type { ReactNode } from 'react';
import { Chip } from '@/components/controls';
import type { AgentPlugin, BenchmarkPlugin, LspPlugin, MetricPlugin, ToolCommand } from '@/lib/types';
import { Note, Panel } from './kit';

/** What a capability lets a setup do with this tool. A setup that needs one the
 *  tool lacks is refused at run creation rather than silently downgraded. */
const CAPABILITY: Record<string, string> = {
  lsp: 'Can drive a language server (S1-LSP)',
  retrieval: 'Can query the retrieval server over MCP (S2, S3)',
  eval_tool: 'Can call the evaluation tool mid-run (S1-eval)',
  subagents: 'Runs its own sub-agents (S3-native)',
};

/** One installed thing. `provides` says what it is for; `state` whether it works. */
function Row({ name, id, provides, state }: {
  name: string;
  id: string;
  provides: ReactNode;
  state: ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 py-1.5">
      <div className="w-52 shrink-0">
        <div className="truncate text-xs text-fg">{name}</div>
        <code className="font-mono text-[11px] text-fg-subtle">{id}</code>
      </div>
      <div className="min-w-0 flex-1 text-[11px] text-fg-muted">{provides}</div>
      <div className="shrink-0 text-right">{state}</div>
    </div>
  );
}

/** Present, or absent with the one command that fixes it. */
function State({ ok, ready, missing, install }: {
  ok: boolean;
  ready: string;
  missing: string;
  install?: string;
}) {
  if (ok) return <Chip mono tone="success" title={ready}>{ready}</Chip>;
  return (
    <span className="inline-flex flex-col items-end gap-0.5">
      <Chip tone="danger" title={missing}>unavailable</Chip>
      {install
        ? <code className="font-mono text-[11px] text-fg-subtle">{install}</code>
        : <span className="text-[11px] text-fg-subtle">{missing}</span>}
    </span>
  );
}

/** The tool an agent plugin drives, as found on this machine. */
export function CommandCell({ command }: { command?: ToolCommand }) {
  if (!command || command.state === 'bundled') {
    return <span className="text-[11px] text-fg-subtle">ships with the plugin</span>;
  }
  if (command.state === 'absent') {
    return <State ok={false} ready="" install={command.install}
      missing={`${command.binary} is not on PATH in this container`} />;
  }
  return <Chip mono tone="success" title={`Reported by ${command.binary} --version`}>
    {command.version || 'installed'}
  </Chip>;
}

export interface PluginsDoc {
  agents: AgentPlugin[];
  benchmarks: BenchmarkPlugin[];
  metrics: MetricPlugin[];
  lsp: LspPlugin[];
}

export function PluginsSection({ plugins, errors }: { plugins: PluginsDoc; errors: string[] }) {
  return (
    <>
      {errors?.length > 0 && (
        <Panel title="Failed to load" description="These directories were skipped, so what they provide is unavailable.">
          {errors.map((e) => <p key={e} className="font-mono text-[11px] text-danger-fg">{e}</p>)}
        </Panel>
      )}

      <Panel title="Agent tools" description="plugins/agents — one AI CLI each. A run cannot start on a tool that is absent.">
        <div className="divide-y divide-border">
          {plugins.agents.map((agent) => (
            <Row key={agent.key} name={agent.name} id={agent.key}
              provides={
                <span className="flex flex-wrap gap-1">
                  {Object.entries(agent.capabilities).filter(([, on]) => on).map(([key]) => (
                    <Chip key={key} mono title={CAPABILITY[key] ?? key}>{key}</Chip>
                  ))}
                  {Object.values(agent.capabilities).every((on) => !on) && 'single agent only'}
                </span>
              }
              state={<CommandCell command={agent.command} />} />
          ))}
        </div>
      </Panel>

      <Panel title="Benchmarks" description="plugins/benchmarks — tasks, their prompt and their scoring pipeline. Data is fetched on the Benchmarks screen.">
        <div className="divide-y divide-border">
          {plugins.benchmarks.map((benchmark) => (
            <Row key={benchmark.key} name={benchmark.name} id={benchmark.key}
              provides={`${benchmark.taskCount.toLocaleString()} ${benchmark.language} task${benchmark.taskCount === 1 ? '' : 's'} · ${benchmark.setups.length} setup${benchmark.setups.length === 1 ? '' : 's'}`}
              state={<State ok={benchmark.dataState === 'ready'} ready="ready"
                missing={`its data is ${benchmark.dataState}; fetch it on the Benchmarks screen`} />} />
          ))}
        </div>
      </Panel>

      <Panel title="Metrics" description="plugins/evaluation — one measurement each, referenced by id from any benchmark's pipeline.">
        <div className="divide-y divide-border">
          {plugins.metrics.map((metric) => (
            <Row key={metric.id} name={metric.title} id={metric.id}
              provides={
                <span className="flex items-center gap-1.5">
                  <Chip mono title={metric.gates
                    ? 'Can fail a task, when a benchmark uses it as a gate'
                    : 'Records numbers only; it can never fail a task'}>
                    {metric.gates ? 'can gate' : 'records only'}
                  </Chip>
                  <span className="line-clamp-1" title={metric.summary}>{metric.summary}</span>
                </span>
              }
              state={<State ok={metric.available} ready="ready" install={metric.install}
                missing={metric.unavailable || `needs ${metric.requires}`} />} />
          ))}
          {plugins.metrics.length === 0 && (
            <Note>No metric is installed, so no benchmark can be scored.</Note>
          )}
        </div>
      </Panel>

      <Panel title="Language servers" description="plugins/lsp — one server per language, offered to the S1-LSP setup.">
        <div className="divide-y divide-border">
          {plugins.lsp.map((server) => (
            <Row key={server.key} name={server.name || server.key} id={server.key}
              provides={`${server.language} · S1-LSP`}
              state={<State ok={server.available} ready="ready"
                missing={`the ${server.key} server is not installed here`} />} />
          ))}
          {plugins.lsp.length === 0 && (
            <Note>No language server is installed, so the S1-LSP setup is unavailable.</Note>
          )}
        </div>
      </Panel>
    </>
  );
}
