'use client';

/**
 * How a task is judged, in the order it happens: the benchmark prepares, stages
 * that can fail it run, measurements are recorded, and a rule decides the verdict.
 *
 * Every stage is drawn by one component, because every metric is one add-on and
 * none is privileged. Each property a stage has — it writes in the workspace, it
 * records these values, it needs something absent here — is a labelled symbol
 * rather than a phrase repeated under each row. Options stay folded away until
 * they are wanted, and each is a control of the declared type with the metric's
 * own default behind it, so restoring one is a click and not a guess at the
 * value to type back.
 */

import { type ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import {
  Braces, ChevronDown, ChevronRight, CircleAlert, CircleCheck, Eye, FolderGit2,
  Gauge, Plus, RotateCcw, Save, ShieldCheck, Sliders, TriangleAlert, Wrench,
} from 'lucide-react';
import { Btn, Select } from '@/components/ui';
import { Chip, Dot, IconBtn, Segmented, SubHeading, Switch } from '@/components/controls';
import type { EvaluationDoc, Metric, OptionRow, Stage, StageConfig } from '@/lib/metrics';
import {
  coerce, defaultExpression, displayValue, optionRows, pipelineChanged,
  requirementLabel, verdictNames, verdictProblem, withOption,
} from '@/lib/metrics';
import { getJson, Note, Panel } from './kit';

const ICON = 'h-3.5 w-3.5 shrink-0';

export function EvaluationSection({ benchmark }: { benchmark: string }) {
  const [doc, setDoc] = useState<EvaluationDoc | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [passed, setPassed] = useState('');
  const [open, setOpen] = useState<string[]>([]);
  const [msg, setMsg] = useState('');
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState(false);

  // guard against a stale response from a previously-selected benchmark
  useEffect(() => {
    let stale = false;
    setDoc(null); setMsg(''); setFailed(false); setOpen([]);
    getJson<EvaluationDoc>(`/api/benchmarks/${benchmark}/evaluation`).then((d) => {
      if (stale || !d) return;
      setDoc(d); setStages(d.effective.verify); setPassed(d.effective.passed);
    });
    return () => { stale = true; };
  }, [benchmark]);

  const names = useMemo(() => verdictNames(stages), [stages]);
  const problem = verdictProblem(passed, names);
  const dirty = doc ? pipelineChanged(doc, stages, passed) : false;

  if (!doc) return <Panel title="Scoring"><Note>Loading…</Note></Panel>;

  function adopt(next: EvaluationDoc) {
    setDoc(next); setStages(next.effective.verify); setPassed(next.effective.passed);
  }

  async function save() {
    setBusy(true); setMsg(''); setFailed(false);
    const res = await fetch(`/api/benchmarks/${benchmark}/evaluation`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        verify: stages.map((s) => ({ preset: s.preset, config: s.config, enabled: s.enabled })),
        passed,
      }),
    });
    setBusy(false);
    if (!res.ok) {
      setFailed(true);
      setMsg((await res.json().catch(() => ({}))).detail ?? `HTTP ${res.status}`);
      return;
    }
    adopt(await res.json());
    setMsg('Saved. The next run uses it.');
  }

  async function reset() {
    setBusy(true); setFailed(false);
    const res = await fetch(`/api/benchmarks/${benchmark}/evaluation`, { method: 'DELETE' });
    setBusy(false);
    if (!res.ok) { setFailed(true); setMsg(`HTTP ${res.status}`); return; }
    adopt(await res.json());
    setMsg('Restored to the values the plugin ships.');
  }

  const patch = (index: number, next: Partial<Stage>) =>
    setStages((all) => all.map((stage, at) => (at === index ? { ...stage, ...next } : stage)));

  const used = new Set([...stages.map((s) => s.preset), ...doc.capture.map((c) => c.id)]);
  const addable = doc.available.filter((metric) => !used.has(metric.id) && metric.gates);

  function add(id: string) {
    const metric = doc!.available.find((m) => m.id === id);
    if (!metric) return;
    setStages((all) => [...all, { preset: id, config: {}, enabled: true, metric }]);
    setOpen((keys) => [...keys, id]);
  }

  return (
    <Panel
      title="Scoring"
      description={`How ${doc.benchmark} judges a task, in the order it happens.`}
      actions={
        <>
          {dirty && <Dot label="unsaved changes" />}
          {doc.overridden && <Chip tone="attention" title="Edited here; the plugin's own values are one click away">edited</Chip>}
          <Btn variant="primary" loading={busy} disabled={!dirty || Boolean(problem)}
            icon={<Save className={ICON} />} onClick={save}>Save</Btn>
          <IconBtn icon={<RotateCcw className={ICON} />} label="Restore the values the plugin ships"
            disabled={!doc.overridden || busy} onClick={reset} />
        </>
      }>
      {doc.prepare && (
        <div className="space-y-2">
          <SubHeading
            icon={<Wrench className={`${ICON} text-fg-muted`} />}
            title="Prepared by the benchmark"
            detail="before anything is measured" />
          <MetricRow metric={doc.prepare}
            lead={<Wrench className={`${ICON} text-fg-subtle`} aria-hidden="true" />} />
        </div>
      )}

      <div className={`${doc.prepare ? 'mt-4 ' : ''}space-y-2`}>
        <SubHeading
          icon={<ShieldCheck className={`${ICON} text-fg-muted`} />}
          title="Can fail a task"
          count={stages.length}
          detail={stages.some((s) => !s.enabled) ? `${stages.filter((s) => !s.enabled).length} switched off` : undefined} />
        {stages.map((stage, index) => (
          <StageCard
            key={stage.preset}
            stage={stage}
            editable
            expanded={open.includes(stage.preset)}
            onExpand={() => setOpen((keys) => (
              keys.includes(stage.preset) ? keys.filter((k) => k !== stage.preset) : [...keys, stage.preset]
            ))}
            onToggle={(enabled) => patch(index, { enabled })}
            onConfig={(config) => patch(index, { config })} />
        ))}
        {stages.length === 0 && <Note>Nothing can fail a task here; every stage only records.</Note>}
        <AddMetric metrics={addable} onAdd={add} />
      </div>

      <div className="mt-4 space-y-2">
        <SubHeading icon={<Eye className={`${ICON} text-fg-muted`} />} title="Recorded" count={doc.capture.length}
          detail="stored with every task, never decides the verdict" />
        {doc.capture.map((metric) => (
          <MetricRow key={metric.id} metric={metric}
            lead={<Eye className={`${ICON} text-fg-subtle`} aria-hidden="true" />} />
        ))}
        {doc.capture.length === 0 && <Note>None.</Note>}
      </div>

      <div className="mt-4">
        <SubHeading icon={<ShieldCheck className={`${ICON} text-fg-muted`} />} title="Verdict" />
        <div className="mt-2">
          <VerdictRule
            passed={passed}
            stages={stages}
            names={names}
            problem={problem}
            editable
            onChange={setPassed} />
        </div>
      </div>

      {msg && (
        <p className="mt-3 flex items-center gap-1.5">
          {failed
            ? <CircleAlert className={`${ICON} text-danger-fg`} aria-hidden="true" />
            : <CircleCheck className={`${ICON} text-success-fg`} aria-hidden="true" />}
          <Note tone={failed ? 'error' : 'ok'}>{msg}</Note>
        </p>
      )}
    </Panel>
  );
}

/**
 * Adding a metric offers what is installed and not already here, and only while
 * adding: a list of everything this benchmark does not use was a permanent
 * column of rows an operator never acted on.
 */
export function AddMetric({ metrics, onAdd }: { metrics: Metric[]; onAdd: (id: string) => void }) {
  const [picking, setPicking] = useState(false);
  if (metrics.length === 0) return null;
  if (!picking) {
    return (
      <Btn variant="invisible" icon={<Plus className={ICON} />} onClick={() => setPicking(true)}>
        Add a metric
      </Btn>
    );
  }
  return (
    <div className="flex items-center gap-2 rounded-md border border-dashed border-border px-2 py-1.5">
      <Select aria-label="Metric to add" defaultValue=""
        onChange={(event) => { if (event.target.value) { onAdd(event.target.value); setPicking(false); } }}
        className="h-7 flex-1 text-xs">
        <option value="" disabled>Choose a metric…</option>
        {metrics.map((metric) => (
          <option key={metric.id} value={metric.id}>
            {metric.title} · {metric.id}{metric.available ? '' : ' (not installed)'}
          </option>
        ))}
      </Select>
      <IconBtn icon={<CircleAlert className="h-3 w-3" />} label="Cancel" onClick={() => setPicking(false)} />
    </div>
  );
}

// ─── The rule ────────────────────────────────────────────────────────────────

/**
 * An empty expression means every enabled stage must pass, which is the rule
 * most benchmarks want and the one that stays correct when a stage is switched
 * off. Choosing it explicitly is therefore a mode rather than an empty field,
 * and the equivalent expression is shown so the choice is not opaque.
 */
export function VerdictRule({ passed, stages, names, problem, editable, onChange }: {
  passed: string;
  stages: Stage[];
  names: string[];
  problem: string;
  editable: boolean;
  onChange: (next: string) => void;
}) {
  const field = useRef<HTMLInputElement>(null);
  const custom = passed.trim() !== '';
  const equivalent = defaultExpression(stages);

  function insert(name: string) {
    const input = field.current;
    if (!input) { onChange(passed ? `${passed} and ${name}` : name); return; }
    const at = input.selectionStart ?? passed.length;
    const to = input.selectionEnd ?? at;
    const pad = at > 0 && !/[\s(]$/.test(passed.slice(0, at)) ? ' ' : '';
    const next = `${passed.slice(0, at)}${pad}${name}${passed.slice(to)}`;
    onChange(next);
    requestAnimationFrame(() => {
      input.focus();
      const caret = at + pad.length + name.length;
      input.setSelectionRange(caret, caret);
    });
  }

  return (
    <div className="rounded-md border border-border bg-canvas-subtle p-2">
      <div className="flex flex-wrap items-center gap-2">
        <Segmented<'all' | 'custom'>
          label="How the verdict is decided"
          value={custom ? 'custom' : 'all'}
          disabled={!editable}
          onChange={(mode) => onChange(mode === 'all' ? '' : (passed || equivalent))}
          options={[
            { value: 'all', label: 'Every stage passes', icon: <ShieldCheck className="h-3 w-3" />, title: 'A task passes when no gating stage failed' },
            { value: 'custom', label: 'Rule', icon: <Braces className="h-3 w-3" />, title: 'Combine stages with and, or, not' },
          ]} />
        {!custom && equivalent && (
          <code className="truncate font-mono text-[11px] text-fg-subtle" title={equivalent}>{equivalent}</code>
        )}
      </div>

      {custom && (
        <>
          <div className="mt-2 flex items-center gap-2">
            <input
              ref={field}
              aria-label="Verdict rule"
              value={passed}
              readOnly={!editable}
              onChange={(event) => onChange(event.target.value)}
              spellCheck={false}
              className={`h-8 flex-1 rounded-md border bg-canvas-inset px-2 font-mono text-xs text-fg outline-none transition-colors ${problem ? 'border-danger-muted focus:border-danger-fg' : 'border-border focus:border-accent-fg'}`} />
            {problem
              ? <CircleAlert className={`${ICON} text-danger-fg`} aria-label="invalid" />
              : <CircleCheck className={`${ICON} text-success-fg`} aria-label="valid" />}
          </div>
          {problem && <p className="mt-1"><Note tone="error">{problem}</Note></p>}
          {editable && names.length > 0 && (
            <div className="mt-1.5 flex flex-wrap items-center gap-1">
              {names.map((name) => (
                <button key={name} type="button" onClick={() => insert(name)}
                  title={`Insert ${name}`}
                  className="rounded-full border border-border bg-canvas px-1.5 py-px font-mono text-[11px] text-fg-muted transition-colors hover:border-fg-muted hover:text-fg">
                  {name}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── One metric, wherever it appears ─────────────────────────────────────────

function RequirementChip({ metric }: { metric: Metric }) {
  if (metric.available) {
    if (!metric.requires) return null;
    return <Chip icon={<Wrench className="h-3 w-3" />} title={requirementLabel(metric)} />;
  }
  return (
    <Chip icon={<TriangleAlert className="h-3 w-3" />} tone="danger" title={requirementLabel(metric)}>
      unavailable
    </Chip>
  );
}

/** What this metric is and what it does, in one line of symbols. */
export function MetricRow({ metric, lead, actions, dimmed, children }: {
  metric: Metric;
  lead?: ReactNode;
  actions?: ReactNode;
  dimmed?: boolean;
  children?: ReactNode;
}) {
  return (
    <div className={`rounded-md border border-border ${dimmed ? 'opacity-70' : ''}`}>
      <div className="px-2 py-1.5">
        <div className="flex items-center gap-2">
          {lead}
          <span className="truncate text-xs font-medium text-fg">{metric.title}</span>
          <code className="hidden truncate font-mono text-[10px] text-fg-subtle sm:inline">{metric.id}</code>
          <span className="ml-auto flex shrink-0 items-center gap-1">
            {metric.reason && (
              <Chip icon={<ShieldCheck className="h-3 w-3" />} mono title={`Fails the task as ${metric.reason}`}>
                {metric.reason}
              </Chip>
            )}
            {metric.mutatesWorkspace && (
              <Chip icon={<FolderGit2 className="h-3 w-3" />} title="Runs inside the task workspace" />
            )}
            {metric.outputs.length > 0 && (
              <Chip icon={<Gauge className="h-3 w-3" />} title={`Records ${metric.outputs.join(', ')}`}>
                {metric.outputs.length}
              </Chip>
            )}
            <RequirementChip metric={metric} />
            {actions}
          </span>
        </div>
        {metric.summary && (
          <p className="mt-1 line-clamp-2 text-[11px] text-fg-muted" title={metric.summary}>{metric.summary}</p>
        )}
      </div>
      {children}
    </div>
  );
}

export function StageCard({ stage, editable, expanded, onExpand, onToggle, onConfig }: {
  stage: Stage;
  editable: boolean;
  expanded: boolean;
  onExpand: () => void;
  onToggle: (enabled: boolean) => void;
  onConfig: (config: StageConfig) => void;
}) {
  const rows = optionRows(stage.metric, stage.config);
  const tuned = rows.filter((row) => row.value !== undefined).length;
  return (
    <MetricRow
      metric={stage.metric}
      dimmed={!stage.enabled}
      lead={<Switch checked={stage.enabled} disabled={!editable} onChange={onToggle}
        label={`Run ${stage.metric.title} on every task`} />}
      actions={rows.length > 0 && (
        <IconBtn
          onClick={onExpand}
          aria-expanded={expanded}
          label={`${expanded ? 'Hide' : 'Show'} ${rows.length} options${tuned ? `, ${tuned} set here` : ''}`}
          icon={(
            <span className="flex items-center gap-0.5">
              <Sliders className="h-3 w-3" />
              <span className="tabular-nums text-[10px]">{rows.length}</span>
              {tuned > 0 && <Dot tone="accent" className="h-1 w-1" />}
              {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            </span>
          )}
          className="w-auto px-1" />
      )}>
      {expanded && rows.length > 0 && (
        <div className="divide-y divide-border border-t border-border">
          {rows.map((row) => (
            <OptionField
              key={row.option.key}
              row={row}
              disabled={!editable}
              onChange={(value) => onConfig(withOption(stage.config, row.option.key, value))} />
          ))}
        </div>
      )}
    </MetricRow>
  );
}

// ─── One option ──────────────────────────────────────────────────────────────

const FIELD = 'h-7 w-full rounded border border-border bg-canvas-inset px-2 font-mono text-[11px] text-fg outline-none focus:border-accent-fg';

export function OptionField({ row, disabled, onChange }: {
  row: OptionRow;
  disabled: boolean;
  onChange: (value: unknown) => void;
}) {
  const { option, value } = row;
  const fallback = displayValue(option.default);
  const id = `opt-${option.key}`;
  const set = value !== undefined;

  return (
    <div className="px-2 py-1.5">
      <div className="flex items-center gap-2">
        <label
          htmlFor={id}
          title={option.help || undefined}
          className={`w-44 shrink-0 truncate text-[11px] ${option.help ? 'cursor-help decoration-dotted underline-offset-2 hover:underline' : ''} ${set ? 'text-fg' : 'text-fg-muted'}`}>
          {option.label}
          {!row.declared && <Chip className="ml-1" tone="attention" title="Configured by the manifest; this metric does not declare it">extra</Chip>}
        </label>

        <div className="relative flex-1">
          {option.type === 'boolean' ? (
            <Switch
              checked={value === undefined ? Boolean(option.default) : Boolean(value)}
              disabled={disabled}
              onChange={onChange}
              label={option.label} />
          ) : option.type === 'choice' ? (
            // Picking the declared default clears the override; picking an empty
            // choice stores it, because "" is a value some metrics accept.
            <Select id={id} disabled={disabled} value={set ? displayValue(value) : fallback}
              onChange={(event) => onChange(event.target.value === fallback ? undefined : event.target.value)}
              className="h-7 w-full font-mono text-[11px]">
              {option.choices.map((choice) => (
                <option key={choice} value={choice}>
                  {choice === '' ? 'none' : choice}{choice === fallback ? ' · default' : ''}
                </option>
              ))}
            </Select>
          ) : (
            <>
              <input
                id={id}
                type={option.type === 'integer' || option.type === 'number' ? 'number' : 'text'}
                step={option.type === 'number' ? 'any' : undefined}
                inputMode={option.type === 'integer' ? 'numeric' : undefined}
                disabled={disabled}
                value={displayValue(value)}
                placeholder={fallback || (option.type === 'reference' ? 'params.<key>' : option.type === 'list' ? 'value, value' : 'unset')}
                onChange={(event) => onChange(coerce(option.type, event.target.value))}
                className={`${FIELD} ${option.unit ? 'pr-14' : ''}`} />
              {option.unit && (
                <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-fg-subtle">
                  {option.unit}
                </span>
              )}
            </>
          )}
        </div>

        <IconBtn
          icon={<RotateCcw className="h-3 w-3" />}
          label={`Restore the default${fallback ? `: ${fallback}` : ''}`}
          disabled={disabled || !set}
          onClick={() => onChange(undefined)} />
      </div>
    </div>
  );
}
