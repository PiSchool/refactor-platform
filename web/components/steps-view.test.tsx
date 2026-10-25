import { describe, expect, it } from 'vitest';
import { toSteps } from './steps-view';

const ev = (type: string, timestamp: string, data: Record<string, unknown> = {}) => ({ type, timestamp, data });

describe('toSteps', () => {
  it('ends session setup where the agent starts, not at shutdown', () => {
    // The shutdown used to extend "Set up session" to the end of the run, so a
    // five-minute session read as five minutes of setup.
    const steps = toSteps([
      ev('session.start', '2026-10-25T01:00:00.000Z', { producer: 'claude' }),
      ev('assistant.turn_start', '2026-10-25T01:00:02.000Z', { turnId: '0' }),
      ev('assistant.turn_end', '2026-10-25T01:04:00.000Z', { turnId: '0' }),
      ev('session.shutdown', '2026-10-25T01:05:00.000Z', { shutdownType: 'completed' }),
    ] as any);
    const setup = steps.find((s) => s.id === 'setup')!;
    expect(setup.endedAt).toBe('2026-10-25T01:00:00.000Z');
    const end = steps.find((s) => s.id === 'end')!;
    expect(end.title).toBe('End session');
    expect(end.detail).toBe('completed');
  });
});
