import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { AgentChoice } from './run-wizard';
import type { AgentCat } from '../lib/types';

/**
 * An agent whose CLI is missing from the backend must be visibly unavailable.
 * Offering it produced a task that died inside the terminal, blamed on the agent.
 */
const installed: AgentCat = {
  id: 'a1', key: 'copilot', name: 'GitHub Copilot CLI', capabilities: {},
  binary: 'copilot', available: true, install: 'npm install -g @github/copilot',
};
const missing: AgentCat = {
  id: 'a2', key: 'aider', name: 'Aider', capabilities: {},
  binary: 'aider', available: false, install: 'python3 -m pip install aider-chat',
};

describe('agent availability in the launch wizard', () => {
  it('offers an agent whose CLI is installed', () => {
    const markup = renderToStaticMarkup(
      <AgentChoice agent={installed} selected={false} onSelect={() => {}} />,
    );
    expect(markup).toContain('GitHub Copilot CLI');
    expect(markup).not.toContain('disabled');
    expect(markup).not.toContain('not installed');
  });

  it('disables an agent whose CLI is missing and shows how to install it', () => {
    const markup = renderToStaticMarkup(
      <AgentChoice agent={missing} selected={false} onSelect={() => {}} />,
    );
    expect(markup).toContain('disabled');
    expect(markup).toContain('is not installed');
    expect(markup).toContain('>aider<');
    expect(markup).toContain('pip install aider-chat');
  });

  it('treats an agent that declares no binary as available', () => {
    const plain: AgentCat = { id: 'a3', key: 'x', name: 'Custom', capabilities: {} };
    const markup = renderToStaticMarkup(
      <AgentChoice agent={plain} selected onSelect={() => {}} />,
    );
    expect(markup).not.toContain('disabled');
    expect(markup).toContain('any provider model');
  });
});
