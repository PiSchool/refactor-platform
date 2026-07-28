import { describe, expect, it } from 'vitest';

import type { EvaluationDoc, Metric, MetricOption, Stage } from './metrics';
import {
  coerce, defaultExpression, displayValue, optionRows, pipelineChanged,
  requirementLabel, verdictNames, verdictProblem, withOption,
} from './metrics';

function option(over: Partial<MetricOption> = {}): MetricOption {
  return { key: 'timeout', label: 'Timeout', type: 'integer', default: 900, help: '', unit: 'seconds', choices: [], ...over };
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

describe('what a metric needs in order to run', () => {
  it('states the requirement, so an absent one is visible before a run', () => {
    expect(requirementLabel(metric())).toBe('Needs pytest in the runtime environment');
    expect(requirementLabel(metric({ requires: '' }))).toBe('');
  });

  it('reports why a metric cannot run here instead of what it would need', () => {
    expect(requirementLabel(metric({ available: false, unavailable: 'codebleu is not installed' })))
      .toBe('codebleu is not installed');
    expect(requirementLabel(metric({ id: 'ghost', available: false, unavailable: '' })))
      .toBe('ghost is not installed');
  });
});

describe('the options a stage offers', () => {
  it('lists every declared option, set or not', () => {
    const rows = optionRows(metric(), {});
    expect(rows).toHaveLength(1);
    expect(rows[0].value).toBeUndefined();
    expect(rows[0].declared).toBe(true);
  });

  it('keeps a configured key the metric does not declare editable', () => {
    const rows = optionRows(metric(), { timeout: 60, legacy_flag: true });
    expect(rows.map((r) => r.option.key)).toEqual(['timeout', 'legacy_flag']);
    expect(rows[1]).toMatchObject({ declared: false, value: true });
    expect(rows[1].option.type).toBe('boolean');
  });

  it('survives a metric that declares nothing', () => {
    expect(optionRows(metric({ options: [] }), undefined)).toEqual([]);
  });
});

describe('reading and writing an option', () => {
  it('shows a list as comma-separated text and parses it back', () => {
    expect(displayValue(['toolz/tests', 'more_itertools'])).toBe('toolz/tests, more_itertools');
    expect(coerce('list', ' toolz/tests , more_itertools ')).toEqual(['toolz/tests', 'more_itertools']);
  });

  it('coerces numbers so a timeout is not saved as a string', () => {
    expect(coerce('integer', '600')).toBe(600);
    expect(coerce('number', '0.5')).toBe(0.5);
    expect(coerce('integer', 'soon')).toBeUndefined();
  });

  it('treats an emptied field as unset, restoring the metric default', () => {
    expect(coerce('integer', '')).toBeUndefined();
    expect(coerce('list', '  ')).toBeUndefined();
    expect(coerce('string', '')).toBeUndefined();
    expect(withOption({ timeout: 60 }, 'timeout', undefined)).toEqual({});
  });

  it('keeps other options untouched when one changes', () => {
    expect(withOption({ timeout: 60, maxfail: 1 }, 'maxfail', 3)).toEqual({ timeout: 60, maxfail: 3 });
  });

  it('shows nothing for an unset option rather than the word undefined', () => {
    expect(displayValue(undefined)).toBe('');
    expect(displayValue(null)).toBe('');
  });
});

function stage(preset: string, enabled = true, config: Record<string, unknown> = {}): Stage {
  return { preset, config, enabled, metric: metric({ id: preset }) };
}

const PIPELINE = [stage('workspace_changed'), stage('pytest_suite'), stage('java_build', false)];

describe('the names a verdict rule may use', () => {
  it('offers each enabled stage once, under the metric id it records', () => {
    expect(verdictNames(PIPELINE)).toEqual(['workspace_changed', 'pytest_suite']);
  });

  it('drops a stage that is switched off, because the rule would never resolve it', () => {
    expect(verdictNames(PIPELINE)).not.toContain('java_build');
  });

  it('spells out the rule an empty expression stands for', () => {
    expect(defaultExpression(PIPELINE)).toBe('workspace_changed and pytest_suite');
  });
});

describe('validating a verdict rule before it is saved', () => {
  const names = verdictNames(PIPELINE);
  const check = (expression: string) => verdictProblem(expression, names);

  it('accepts an empty rule, which means every enabled stage must pass', () => {
    expect(check('')).toBe('');
    expect(check('   ')).toBe('');
  });

  it('accepts the operators the server evaluates', () => {
    expect(check('workspace_changed and pytest_suite')).toBe('');
    expect(check('not pytest_suite or (workspace_changed and pytest_suite)')).toBe('');
    expect(check('True')).toBe('');
  });

  it('names a stage that no longer exists instead of failing on save', () => {
    expect(check('workspace_changed and refactoring_miner')).toBe('unknown stage "refactoring_miner"');
  });

  it('refuses a stage the operator switched off, which would always be unknown', () => {
    expect(check('java_build')).toBe('unknown stage "java_build"');
  });

  it('reports an unfinished rule while it is still being typed', () => {
    expect(check('workspace_changed and')).toBe('expected a stage name');
    expect(check('and pytest_suite')).toBe('expected a stage name');
  });

  it('reports unbalanced parentheses on the side they are missing from', () => {
    expect(check('(workspace_changed and pytest_suite')).toBe('unclosed "("');
    expect(check('workspace_changed)')).toBe('unmatched ")"');
  });

  it('rejects anything that is not part of the grammar', () => {
    expect(check('workspace_changed && pytest_suite')).toBe('unexpected character "&"');
    expect(check('workspace_changed pytest_suite')).toBe('unexpected "pytest_suite"');
  });
});

describe('knowing whether the pipeline has unsaved edits', () => {
  const doc: EvaluationDoc = {
    benchmark: 'swe',
    overridden: false,
    prepare: null,
    capture: [],
    shipped: { verify: [], passed: '' },
    effective: { verify: [stage('pytest_suite', true, { timeout: 900 })], passed: 'pytest_suite' },
    available: [],
  };

  it('reports no change for the pipeline as it was received', () => {
    expect(pipelineChanged(doc, doc.effective.verify, doc.effective.passed)).toBe(false);
  });

  it('sees a switched-off stage, a changed option and a changed rule', () => {
    expect(pipelineChanged(doc, [stage('pytest_suite', false, { timeout: 900 })], 'pytest_suite')).toBe(true);
    expect(pipelineChanged(doc, [stage('pytest_suite', true, { timeout: 60 })], 'pytest_suite')).toBe(true);
    expect(pipelineChanged(doc, doc.effective.verify, '')).toBe(true);
  });

  it('ignores key order and surrounding space, which are not edits', () => {
    const reordered = stage('pytest_suite', true, { timeout: 900 });
    expect(pipelineChanged(doc, [reordered], '  pytest_suite  ')).toBe(false);
  });
});
