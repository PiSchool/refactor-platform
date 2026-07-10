import { describe, expect, it } from 'vitest';
import { costUsd, formatUsd } from './cost';
import { tone } from './log';

const model = (pricing: Record<string, string>) => ({ id: 'm', name: 'M', contextLength: 1, free: false, pricing });
const usage = { inputTokens: 258453, outputTokens: 3252, cacheReadTokens: 30300 };

describe('costUsd', () => {
  it('never multiplies OpenRouter\'s -1 "price varies" sentinel into a negative cost', () => {
    // openrouter/auto, /fusion, /bodybuilder, /pareto-code all publish -1
    expect(costUsd(usage, model({ prompt: '-1', completion: '-1' }))).toBeNull();
    expect(formatUsd(costUsd(usage, model({ prompt: '-1', completion: '-1' })))).toBe('—');
  });

  it('bills cacheRead at the cheaper rate and subtracts it from input', () => {
    const cost = costUsd(usage, model({ prompt: '0.000003', completion: '0.000015', input_cache_read: '0.0000003' }))!;
    expect(cost).toBeCloseTo(0.742329, 6);
  });

  it('reports a genuinely free model as free, not as unknown', () => {
    expect(formatUsd(costUsd(usage, model({ prompt: '0', completion: '0' })))).toBe('free');
  });

  it('falls back to the prompt rate when cache reads are not priced separately', () => {
    const cost = costUsd(usage, model({ prompt: '0.000001', completion: '0' }))!;
    expect(cost).toBeCloseTo(258453 * 0.000001, 9);
  });
});

describe('tone (errors & warnings filter)', () => {
  it('flags a shell failure that uses none of Maven\'s vocabulary', () => {
    expect(tone('/bin/sh: 1: Syntax error: Unterminated quoted string')).toBe('text-danger-fg');
  });

  it('still flags Maven and Python failures', () => {
    expect(tone('[ERROR] Failed to execute goal')).toBe('text-danger-fg');
    expect(tone('Traceback (most recent call last):')).toBe('text-danger-fg');
    expect(tone('[WARNING] Tests run: 2032, Failures: 0, Errors: 0, Skipped: 15')).not.toBe('text-danger-fg');
  });

  it('does not paint a clean test summary red just because it says "Errors"', () => {
    expect(tone('Tests run: 2032, Failures: 0, Errors: 0, Skipped: 15')).toBe('text-success-fg');
    expect(tone('Tests run: 10, Failures: 2, Errors: 0')).toBe('text-danger-fg');
  });
});
