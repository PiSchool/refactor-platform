import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { ChecksPanel } from './checks-panel';

describe('ChecksPanel', () => {
  it('renders only evaluation stages, not auxiliary retrieval metadata', () => {
    const html = renderToStaticMarkup(
      createElement(ChecksPanel, {
        benchmarkKey: 'refbench',
        task: {
          status: 'passed',
          result: {
            agentSeconds: 163,
            evaluateSeconds: 0.4,
            details: {
              workspace_changed: { ok: true, message: '2 files changed.' },
              python_tests: { ok: true, message: '5/5 tests passed.' },
              retrieval: { strategy: 'ast', preInjected: true, hits: 12 },
            },
          },
        },
      }),
    );

    expect(html).toContain('workspace_changed');
    expect(html).toContain('python_tests');
    expect(html).toContain('2/2 passing');
    expect(html).not.toContain('>retrieval<');
    expect(html).not.toContain('Waiting for the agent to finish.');
  });
});