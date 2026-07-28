import { describe, expect, it } from 'vitest';

import type { PromptVariable } from './types';
import {
  insertToken, isPresent, missingRequired, placeholderFor, syntaxGlyph, syntaxTitle, variableRows,
} from './prompts';

function variable(over: Partial<PromptVariable> = {}): PromptVariable {
  return { name: 'code_to_refactor', summary: 'The source the agent must change', required: true, present: true, ...over };
}

const VARIABLES = [
  variable(),
  variable({ name: 'refactoring_type', summary: 'The operation to apply', required: true }),
  variable({ name: 'retrieved_context', summary: 'Retrieved snippets, when the setup provides them', required: false }),
];

describe('how a value is written into a template', () => {
  it('uses the form the declared syntax renders', () => {
    expect(placeholderFor('format', 'code_to_refactor')).toBe('{code_to_refactor}');
    expect(placeholderFor('jinja', 'code_to_refactor')).toBe('{{ code_to_refactor }}');
  });

  it('labels the syntax with its own brackets, and says nothing when none is declared', () => {
    expect(syntaxGlyph('format')).toBe('{ }');
    expect(syntaxGlyph('jinja')).toBe('{{ }}');
    expect(syntaxGlyph('')).toBe('');
    expect(syntaxTitle('')).toContain('no template syntax');
  });
});

describe('whether the template still contains a value', () => {
  it('requires the placeholder form for a format template', () => {
    expect(isPresent('Refactor {code_to_refactor} now', 'format', 'code_to_refactor')).toBe(true);
    expect(isPresent('Refactor the code_to_refactor now', 'format', 'code_to_refactor')).toBe(false);
  });

  it('accepts the bare name for a Jinja template, where it can appear in any expression', () => {
    expect(isPresent('{% if code_to_refactor %}x{% endif %}', 'jinja', 'code_to_refactor')).toBe(true);
  });
});

describe('the state of each declared value', () => {
  const rows = (content: string) => variableRows(content, 'format', VARIABLES);

  it('marks a required value that is gone, and never blocks on an optional one', () => {
    const state = Object.fromEntries(rows('{code_to_refactor}').map((row) => [row.name, row.state]));
    expect(state).toEqual({
      code_to_refactor: 'present',
      refactoring_type: 'missing',
      retrieved_context: 'unused',
    });
    expect(missingRequired(rows('{code_to_refactor}'))).toEqual(['refactoring_type']);
  });

  it('blocks nothing once every required value is back', () => {
    expect(missingRequired(rows('{code_to_refactor} {refactoring_type}'))).toEqual([]);
  });

  it('carries the placeholder for each value, so it can be reinserted', () => {
    expect(rows('').map((row) => row.placeholder)).toEqual([
      '{code_to_refactor}', '{refactoring_type}', '{retrieved_context}',
    ]);
  });
});

describe('putting a value back into the text', () => {
  it('inserts at the caret and reports where the caret belongs', () => {
    expect(insertToken('Refactor  now', 9, 9, '{code}')).toEqual({ text: 'Refactor {code} now', caret: 15 });
  });

  it('replaces a selection rather than duplicating it', () => {
    expect(insertToken('Refactor XXX now', 9, 12, '{code}')).toEqual({ text: 'Refactor {code} now', caret: 15 });
  });

  it('survives a caret position the textarea never reported', () => {
    expect(insertToken('abc', -5, 99, '{x}').text).toBe('{x}');
    expect(insertToken('abc', 99, 99, '{x}').text).toBe('abc{x}');
  });
});
