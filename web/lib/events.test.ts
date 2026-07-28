import { describe, expect, it } from 'vitest';
import { liveUsage, summarize, type AgentEvent } from './events';

const ev = (type: string, data: Record<string, unknown> = {}): AgentEvent => ({ type, data });

describe('liveUsage', () => {
  it('streams output tokens, turns and compactions while the session runs', () => {
    const u = liveUsage([
      ev('assistant.message', { outputTokens: 100, content: 'x'.repeat(4000) }),
      ev('tool.execution_complete', { result: { content: 'y'.repeat(40000) } }),
      ev('session.compaction_complete', { success: true }),
      ev('assistant.message', { outputTokens: 50 }),
    ]);
    expect(u.outputTokens).toBe(150);
    expect(u.turns).toBe(2);
    expect(u.compactions).toBe(1);
  });

  it('reports no prompt tokens, context or cost basis before shutdown — however big the conversation', () => {
    const u = liveUsage([ev('assistant.message', { outputTokens: 9, content: 'z'.repeat(400_000) })]);
    expect(u.final).toBeNull(); // never inferred from message sizes
  });

  it('ignores failed compactions', () => {
    expect(liveUsage([ev('session.compaction_complete', { success: false })]).compactions).toBe(0);
  });

  it('takes exact prompt tokens and context occupancy from session.shutdown', () => {
    const u = liveUsage([
      ev('assistant.message', { outputTokens: 6200 }),
      ev('session.shutdown', {
        currentTokens: 45921,
        modelMetrics: { 'deepseek/deepseek-v4-pro': { usage: { inputTokens: 614426, cacheReadTokens: 377216, reasoningTokens: 2200 } } },
      }),
    ]);
    expect(u.final).toEqual({ inputTokens: 614426, cacheReadTokens: 377216, reasoningTokens: 2200, contextTokens: 45921 });
    expect(u.outputTokens).toBe(6200);
  });
});

describe('the session label', () => {
  it('names the tool and the version it reported', () => {
    expect(summarize({ type: 'session.start', timestamp: '', data: { producer: 'junie', version: '26.7.20', selectedModel: 'openrouter/free' } } as any))
      .toBe('junie v26.7.20 · model openrouter/free');
  });

  it("still reads Copilot's own name for the same field", () => {
    expect(summarize({ type: 'session.start', timestamp: '', data: { producer: 'copilot-agent', copilotVersion: '1.0.75', selectedModel: 'openrouter/free' } } as any))
      .toBe('copilot-agent v1.0.75 · model openrouter/free');
  });

  it('omits the version when the tool did not report one', () => {
    expect(summarize({ type: 'session.start', timestamp: '', data: { producer: 'opencode', selectedModel: 'openrouter/free' } } as any))
      .toBe('opencode · model openrouter/free');
  });
});
