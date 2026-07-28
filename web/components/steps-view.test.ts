import { describe, expect, it } from 'vitest';

import type { AgentEvent } from '../lib/events';
import { clipped, toSteps } from './steps-view';

function event(type: string, turnId: number, data: Record<string, unknown> = {}): AgentEvent {
  return {
    type,
    timestamp: `2026-07-24T16:53:${String(turnId).padStart(2, '0')}Z`,
    data: { turnId, ...data },
  };
}

describe('agent step grouping', () => {
  it('uses unique chronological turn identities when Copilot resets its raw turn id', () => {
    const steps = toSteps([
      event('assistant.turn_start', 0),
      event('assistant.message', 0, { toolRequests: [{ name: 'view' }] }),
      event('assistant.turn_end', 0),
      event('assistant.turn_start', 1),
      event('assistant.turn_end', 1),
      event('assistant.turn_start', 0),
      event('assistant.message', 0, { toolRequests: [{ name: 'task_complete' }] }),
      event('assistant.turn_end', 0),
    ]);

    expect(steps.map(({ id, title }) => ({ id, title }))).toEqual([
      { id: 'turn-0', title: 'Turn 0' },
      { id: 'turn-1', title: 'Turn 1' },
      { id: 'turn-2', title: 'Turn 2' },
    ]);
    expect(steps[0].detail).toBe('view');
    expect(steps[2].detail).toBe('task_complete');
  });

  it('keeps an oversized reply readable and says how much it is not showing', () => {
    const reply = Array.from({ length: 500 }, (_, i) => `line ${i}`).join('\n');
    const steps = toSteps([
      event('assistant.turn_start', 0),
      event('assistant.message', 0, { content: reply }),
      event('assistant.turn_end', 0),
    ]);

    expect(steps[0].lines).toHaveLength(2);
    expect(steps[0].lines[0].text.split('\n')).toHaveLength(40);
    expect(steps[0].lines[1].text).toBe('[460 more lines — the full text is under Output]');
    expect(steps[0].lines[1].tone).toBe('muted');
  });
});

describe('clipping one reply', () => {
  it('leaves a reply that already fits untouched', () => {
    expect(clipped('two\nlines')).toEqual({ text: 'two\nlines', omitted: '' });
  });

  it('counts characters when a single line is longer than the budget', () => {
    const { text, omitted } = clipped('x'.repeat(5000));
    expect(text).toHaveLength(4000);
    expect(omitted).toBe('[1,000 more characters — the full text is under Output]');
  });
});