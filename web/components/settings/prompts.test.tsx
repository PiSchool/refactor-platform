import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { TemplateList, VariableChip } from './prompts';
import { variableRows } from '@/lib/prompts';
import type { PromptInfo, PromptVariable } from '@/lib/types';

const TEMPLATES: PromptInfo[] = [
  { name: 'extract_method', overridden: false, appliesTo: 'refactoringType = Extract Method', syntax: 'format' },
  { name: 'default', overridden: true, appliesTo: 'every other task', syntax: 'format' },
];

function variable(over: Partial<PromptVariable> = {}): PromptVariable {
  return { name: 'code_to_refactor', summary: 'The source the agent must change', required: true, present: true, ...over };
}

const noop = () => {};

describe('choosing a template', () => {
  it('shows every template as its own row, with the selected one marked', () => {
    const markup = renderToStaticMarkup(
      <TemplateList prompts={TEMPLATES} selected="default" onSelect={noop} />,
    );
    expect(markup).toContain('extract_method');
    expect(markup).toContain('aria-current="true"');
    expect(markup.match(/<button/g)).toHaveLength(2);
  });

  it('marks an edited template without repeating the word in every row', () => {
    const markup = renderToStaticMarkup(
      <TemplateList prompts={TEMPLATES} selected="default" onSelect={noop} />,
    );
    expect(markup).toContain('aria-label="edited here"');
    expect(markup.match(/edited here/g)).toHaveLength(2);   // the marker's label and title
  });

  it('states which tasks select a template on hover, rather than in the row', () => {
    const markup = renderToStaticMarkup(
      <TemplateList prompts={TEMPLATES} selected="" onSelect={noop} />,
    );
    expect(markup).toContain('extract_method — used for refactoringType = Extract Method');
  });
});

describe('a value the benchmark substitutes', () => {
  const rows = (content: string, variables: PromptVariable[]) => variableRows(content, 'format', variables);

  it('is confirmed when the template still contains it, and is not offered for insertion', () => {
    const [row] = rows('{code_to_refactor}', [variable()]);
    const markup = renderToStaticMarkup(<VariableChip row={row} onInsert={noop} />);
    expect(markup).toContain('code_to_refactor');
    expect(markup).toContain('in the template');
    expect(markup).not.toContain('<button');
  });

  it('is offered for insertion, with its placeholder, once it is missing', () => {
    const [row] = rows('nothing here', [variable()]);
    const markup = renderToStaticMarkup(<VariableChip row={row} onInsert={noop} />);
    expect(markup).toContain('<button');
    expect(markup).toContain('{code_to_refactor}');
    expect(markup).toContain('Click to insert it.');
  });

  it('never offers insertion to a reader who cannot mutate', () => {
    const [row] = rows('nothing here', [variable()]);
    expect(renderToStaticMarkup(<VariableChip row={row} />)).not.toContain('<button');
  });

  it('distinguishes an optional value the template does not use from a missing required one', () => {
    const [optional] = rows('nothing here', [variable({ name: 'retrieved_context', required: false })]);
    const markup = renderToStaticMarkup(<VariableChip row={optional} onInsert={noop} />);
    expect(markup).toContain('optional, not used by this template');
    expect(markup).not.toContain('required');
  });
});
