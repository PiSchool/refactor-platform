import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { SystemRows } from './services';
import { withDashboardRow } from '@/lib/build';
import type { SystemGroup } from '@/lib/build';

const deployment: SystemGroup = {
  key: 'deployment',
  title: 'Deployment',
  detail: 'What each container was built from.',
  rows: [{ name: 'Backend', value: '0d280aa01c4f', detail: 'source fingerprint · built 2026-07-26T20:22:18Z' }],
};

describe('the Services screen reports what is deployed', () => {
  it('shows both halves of a redeploy with what each was built from', () => {
    const [group] = withDashboardRow([deployment], {
      fingerprint: '2b8c6aa99d29', revision: 'fd9ac76', builtAt: '2026-07-26T20:22:10Z', buildId: 'Q-KgBBGHAHBpf0w7g3SS1',
    });
    const html = renderToStaticMarkup(<SystemRows rows={group.rows} />);

    expect(html).toContain('Backend');
    expect(html).toContain('0d280aa01c4f');
    expect(html).toContain('Dashboard');
    expect(html).toContain('2b8c6aa99d29');
    expect(html).toContain('revision fd9ac76');
  });

  it('keeps saying an absent tool is not installed', () => {
    const html = renderToStaticMarkup(<SystemRows rows={[
      { name: 'Aider', value: 'absent', state: 'absent', neededBy: 'runs with aider', install: 'pip install aider-chat' },
    ]} />);

    expect(html).toContain('not installed');
    expect(html).toContain('needed for runs with aider');
    expect(html).toContain('pip install aider-chat');
  });
});
