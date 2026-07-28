import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { MetricRow, OptionField, StageCard, VerdictRule } from './evaluation';
import type { Metric, MetricOption, OptionRow, Stage } from '@/lib/metrics';
import { optionRows, verdictNames, verdictProblem } from '@/lib/metrics';

function option(over: Partial<MetricOption> = {}): MetricOption {
  return { key: 'timeout', label: 'Timeout', type: 'integer', default: 900, help: 'Give up after this long.', unit: 's', choices: [], ...over };
}

function metric(over: Partial<Metric> = {}): Metric {
  return {
    id: 'pytest_suite',
    title: 'Repository test suite',
    summary: 'Runs the tests that live in the repository under test.',
    requires: 'pytest in the runtime environment',
    gates: true,
    reason: 'test_failed',
    mutatesWorkspace: true,
    outputs: ['passed', 'failed'],
    options: [option()],
    available: true,
    unavailable: '',
    ...over,
  };
}

function stage(over: Partial<Stage> = {}): Stage {
  return { preset: 'pytest_suite', config: {}, enabled: true, metric: metric(), ...over };
}

const noop = () => {};

describe('a metric row states what the metric does', () => {
  it('carries the id, the failure reason, the recorded count and what it needs', () => {
    const markup = renderToStaticMarkup(<MetricRow metric={metric()} />);
    expect(markup).toContain('Repository test suite');
    expect(markup).toContain('pytest_suite');
    expect(markup).toContain('test_failed');
    expect(markup).toContain('Fails the task as test_failed');
    expect(markup).toContain('Records passed, failed');
    expect(markup).toContain('Runs inside the task workspace');
    expect(markup).toContain('Needs pytest in the runtime environment');
  });

  it('says why a metric cannot run here rather than showing it as ready', () => {
    const markup = renderToStaticMarkup(
      <MetricRow metric={metric({ available: false, unavailable: 'the codebleu library is not installed' })} />,
    );
    expect(markup).toContain('unavailable');
    expect(markup).toContain('the codebleu library is not installed');
  });

  it('leaves out the summary line when there is no summary', () => {
    const markup = renderToStaticMarkup(<MetricRow metric={metric({ summary: '' })} />);
    expect(markup).not.toContain('line-clamp-2');
  });
});

describe('a gating stage', () => {
  it('is switched with a control that announces its state', () => {
    const markup = renderToStaticMarkup(
      <StageCard stage={stage()} editable expanded={false} onExpand={noop} onToggle={noop} onConfig={noop} />,
    );
    expect(markup).toContain('role="switch"');
    expect(markup).toContain('aria-checked="true"');
    expect(markup).toContain('Run Repository test suite on every task');
  });

  it('keeps its options folded away, and says how many there are', () => {
    const markup = renderToStaticMarkup(
      <StageCard stage={stage()} editable expanded={false} onExpand={noop} onToggle={noop} onConfig={noop} />,
    );
    expect(markup).toContain('Show 1 options');
    expect(markup).not.toContain('Timeout');
  });

  it('reports how many options were set here, not merely that some were', () => {
    const markup = renderToStaticMarkup(
      <StageCard stage={stage({ config: { timeout: 60 } })} editable expanded={false}
        onExpand={noop} onToggle={noop} onConfig={noop} />,
    );
    expect(markup).toContain('1 set here');
  });

  it('shows the option controls once expanded', () => {
    const markup = renderToStaticMarkup(
      <StageCard stage={stage()} editable expanded onExpand={noop} onToggle={noop} onConfig={noop} />,
    );
    expect(markup).toContain('Timeout');
    expect(markup).toContain('aria-expanded="true"');
  });

  it('shows a reader who cannot mutate the same state, with every control disabled', () => {
    const markup = renderToStaticMarkup(
      <StageCard stage={stage()} editable={false} expanded onExpand={noop} onToggle={noop} onConfig={noop} />,
    );
    expect(markup).toContain('role="switch"');
    expect(markup).toContain('aria-checked="true"');
    expect(markup).toContain('disabled=""');
  });
});

describe('one option', () => {
  const row = (over: Partial<MetricOption> = {}, value?: unknown): OptionRow =>
    optionRows(metric({ options: [option(over)] }), value === undefined ? {} : { [over.key ?? 'timeout']: value })[0];

  it('shows the metric default as the placeholder and the unit inside the field', () => {
    const markup = renderToStaticMarkup(<OptionField row={row()} disabled={false} onChange={noop} />);
    expect(markup).toContain('placeholder="900"');
    expect(markup).toContain('>s<');
  });

  it('offers to restore the default only when a value was set here', () => {
    const unset = renderToStaticMarkup(<OptionField row={row()} disabled={false} onChange={noop} />);
    const set = renderToStaticMarkup(
      <OptionField row={optionRows(metric(), { timeout: 60 })[0]} disabled={false} onChange={noop} />,
    );
    expect(unset).toContain('Restore the default: 900');
    expect(unset).toContain('disabled=""');
    expect(set).toContain('value="60"');
    expect(set).not.toContain('disabled=""');
  });

  it('renders a declared choice as a list that marks which value is the default', () => {
    const markup = renderToStaticMarkup(
      <OptionField
        row={row({ key: 'compat_shim', label: 'Compatibility shim', type: 'choice', default: '', unit: '', choices: ['', 'py39_ast'] })}
        disabled={false} onChange={noop} />,
    );
    expect(markup).toContain('<select');
    expect(markup).toContain('none');
    expect(markup).toContain('py39_ast');
    expect(markup).toContain('· default');
  });

  it('renders a boolean as a switch that follows the default until it is set', () => {
    const markup = renderToStaticMarkup(
      <OptionField row={row({ key: 'strict', label: 'Strict', type: 'boolean', default: true, unit: '' })}
        disabled={false} onChange={noop} />,
    );
    expect(markup).toContain('role="switch"');
    expect(markup).toContain('aria-checked="true"');
  });

  it('marks a configured key the metric does not declare', () => {
    const extra = optionRows(metric({ options: [] }), { legacy_flag: true })[0];
    const markup = renderToStaticMarkup(<OptionField row={extra} disabled={false} onChange={noop} />);
    expect(markup).toContain('extra');
    expect(markup).toContain('does not declare it');
  });
});

describe('the verdict rule', () => {
  const stages = [stage({ preset: 'workspace_changed', metric: metric({ id: 'workspace_changed' }) }), stage()];
  const names = verdictNames(stages);

  it('shows the rule an empty expression stands for, so the choice is not opaque', () => {
    const markup = renderToStaticMarkup(
      <VerdictRule passed="" stages={stages} names={names} problem="" editable onChange={noop} />,
    );
    expect(markup).toContain('aria-selected="true"');
    expect(markup).toContain('workspace_changed and pytest_suite');
  });

  it('reports an invalid rule beside the field instead of failing on save', () => {
    const passed = 'workspace_changed and refactoring_miner';
    const problem = verdictProblem(passed, names);
    const markup = renderToStaticMarkup(
      <VerdictRule passed={passed} stages={stages} names={names} problem={problem} editable onChange={noop} />,
    );
    expect(markup).toContain('aria-label="invalid"');
    expect(markup).toContain('unknown stage &quot;refactoring_miner&quot;');
  });

  it('confirms a rule that holds', () => {
    const markup = renderToStaticMarkup(
      <VerdictRule passed="workspace_changed" stages={stages} names={names} problem="" editable onChange={noop} />,
    );
    expect(markup).toContain('aria-label="valid"');
  });

  it('offers each usable stage name for insertion, and none to a read-only reader', () => {
    const editable = renderToStaticMarkup(
      <VerdictRule passed="suite" stages={stages} names={names} problem="" editable onChange={noop} />,
    );
    const readOnly = renderToStaticMarkup(
      <VerdictRule passed="suite" stages={stages} names={names} problem="" editable={false} onChange={noop} />,
    );
    expect(editable).toContain('Insert workspace_changed');
    expect(readOnly).not.toContain('Insert workspace_changed');
    expect(readOnly).toMatch(/readonly=""/i);
  });
});
