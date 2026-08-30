import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { CommandCell, PluginsSection } from './plugins';
import type { PluginsDoc } from './plugins';

const doc: PluginsDoc = {
  agents: [
    {
      key: 'copilot',
      name: 'GitHub Copilot CLI',
      capabilities: { lsp: true, retrieval: true, subagents: true, eval_tool: true },
      command: { binary: 'copilot', state: 'ok', version: '1.0.75', install: '' },
    },
    {
      key: 'aider',
      name: 'Aider',
      capabilities: { eval_tool: true, retrieval: false },
      command: { binary: 'aider', state: 'absent', version: '', install: 'pip install aider-chat' },
    },
  ],
  benchmarks: [{
    key: 'swe', name: 'SWE-Refactor', language: 'java', taskCount: 1099,
    dataState: 'ready', dataError: '', setups: ['s1', 's2_rag'],
  }],
  metrics: [
    {
      id: 'java_build', title: 'Java build and test', summary: 'Compiles the project and runs its suite.',
      requires: 'a JDK and Maven or Gradle', gates: true, reason: 'compile_test_failed',
      mutatesWorkspace: true, outputs: ['testsPassed'], options: [],
      available: true, unavailable: '', install: '',
    },
    {
      id: 'codebleu', title: 'CodeBLEU similarity', summary: 'Scores the file against a reference.',
      requires: 'the codebleu library', gates: false, reason: '',
      mutatesWorkspace: false, outputs: ['codebleu'], options: [],
      available: false, unavailable: 'the codebleu library is not installed',
      install: 'pip install codebleu',
    },
  ],
  lsp: [{ key: 'jdtls', name: 'Eclipse JDT', language: 'java', available: true }],
};

describe('the inventory of what is installed', () => {
  it('states the version the command answers with, not one written in a manifest', () => {
    // The Copilot manifest declared 1.0.68 while the image shipped 1.0.75, and
    // a finished run recorded the manifest's number as the version that ran.
    const html = renderToStaticMarkup(<PluginsSection plugins={doc} errors={[]} />);
    expect(html).toContain('1.0.75');
    expect(html).not.toContain('v1.0.0');
    expect(html).not.toMatch(/v\d+\.\d+\.\d+/);
  });

  it('says how to install a tool that is missing, in place of a version', () => {
    const html = renderToStaticMarkup(
      <CommandCell command={{ binary: 'aider', state: 'absent', version: '', install: 'pip install aider-chat' }} />,
    );
    expect(html).toContain('unavailable');
    expect(html).toContain('pip install aider-chat');
  });

  it('does not call a bundled tool missing', () => {
    // An adapter may drive something it ships itself; there is no command to find.
    const html = renderToStaticMarkup(
      <CommandCell command={{ binary: '', state: 'bundled', version: '', install: '' }} />,
    );
    expect(html).toContain('ships with the plugin');
    expect(html).not.toContain('unavailable');
  });

  it('reports each tool once, with language servers among the plugins', () => {
    const html = renderToStaticMarkup(<PluginsSection plugins={doc} errors={[]} />);
    expect(html.match(/GitHub Copilot CLI/g)).toHaveLength(1);
    expect(html).toContain('Eclipse JDT');
  });

  it('lists every kind of plugin in one inventory, benchmarks and metrics included', () => {
    const html = renderToStaticMarkup(<PluginsSection plugins={doc} errors={[]} />);
    expect(html).toContain('SWE-Refactor');
    expect(html).toContain('1,099 java tasks');
    expect(html).toContain('Java build and test');
    expect(html).toContain('java_build');
  });

  it('says whether a metric can decide a verdict or only records numbers', () => {
    const html = renderToStaticMarkup(<PluginsSection plugins={doc} errors={[]} />);
    expect(html).toContain('can gate');
    expect(html).toContain('records only');
  });

  it('names what an unavailable metric needs, and the command that installs it', () => {
    // Discovering this in a failed run costs a task; discovering it here costs nothing.
    const html = renderToStaticMarkup(<PluginsSection plugins={doc} errors={[]} />);
    expect(html).toContain('the codebleu library is not installed');
    expect(html).toContain('pip install codebleu');
  });

  it('configures nothing: this screen is an inventory', () => {
    const html = renderToStaticMarkup(<PluginsSection plugins={doc} errors={[]} />);
    expect(html).not.toContain('<input');
    expect(html).not.toContain('<select');
    expect(html).not.toContain('role="switch"');
  });
});
