import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { OutputView } from './output-view';
import { findArtifact } from '../lib/api';

const logRef = {
  key: 'eval-log:python_tests',
  available: true,
  mediaType: 'text/plain',
  sizeBytes: 42,
  viewUrl: '/api/runs/run-1/tasks/task-1/artifacts/eval-log:python_tests',
  downloadUrl: '/api/runs/run-1/tasks/task-1/artifacts/eval-log:python_tests?download=1',
};

const evidenceRefs = [
  {
    ...logRef,
    key: 'prompt',
    mediaType: 'text/markdown',
    viewUrl: '/api/runs/run-1/tasks/task-1/artifacts/prompt',
    downloadUrl: '/api/runs/run-1/tasks/task-1/artifacts/prompt?download=1',
  },
  {
    ...logRef,
    key: 'retrieval-context',
    mediaType: 'text/markdown',
    viewUrl: '/api/runs/run-1/tasks/task-1/artifacts/retrieval-context',
    downloadUrl: '/api/runs/run-1/tasks/task-1/artifacts/retrieval-context?download=1',
  },
  {
    ...logRef,
    key: 'self-check:0001:result',
    mediaType: 'application/json',
    viewUrl: '/api/runs/run-1/tasks/task-1/artifacts/self-check:0001:result',
    downloadUrl: '/api/runs/run-1/tasks/task-1/artifacts/self-check:0001:result?download=1',
  },
];

describe('identity-scoped evidence', () => {
  it('renders evaluation output using the server-provided stable URL', () => {
    const html = renderToStaticMarkup(createElement(OutputView, {
      artifacts: [logRef],
      stages: { python_tests: { ok: true } },
    }));

    expect(html).toContain(logRef.downloadUrl.replaceAll('&', '&amp;'));
    expect(html).not.toContain('/api/artifact?path=');
    expect(html).not.toContain('/workspace/');
  });

  it('uses stable references for prompt, retrieval, and self-check evidence', () => {
    expect(findArtifact(evidenceRefs, 'prompt')?.viewUrl).toBe(evidenceRefs[0].viewUrl);
    expect(findArtifact(evidenceRefs, 'retrieval-context')?.viewUrl).toBe(evidenceRefs[1].viewUrl);

    const html = renderToStaticMarkup(createElement(OutputView, {
      artifacts: [evidenceRefs[2]],
    }));
    expect(html).toContain(evidenceRefs[2].downloadUrl);
    expect(html).toContain('self-check 0001 result');
  });

  it('does not resolve unavailable evidence', () => {
    expect(findArtifact([{ ...evidenceRefs[0], available: false }], 'prompt')).toBeUndefined();
  });

  it('contains no legacy path-selected evidence requests in run detail consumers', () => {
    const files = [
      join(process.cwd(), 'app', 'runs', '[id]', 'page.tsx'),
      join(process.cwd(), 'components', 'output-view.tsx'),
      join(process.cwd(), 'components', 'terminal.tsx'),
    ];
    const source = files.map((file) => readFileSync(file, 'utf-8')).join('\n');

    expect(source).not.toContain('/api/artifact?path=');
    expect(source).not.toContain('/workspace/');
    expect(source).not.toContain('workspacePath');
    expect(source).not.toContain('/api/sessions/${sessionId}/terminal-log');
    expect(source).toContain('.viewUrl');
    expect(source).toContain('.downloadUrl');
  });
});