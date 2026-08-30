/**
 * Reading a prompt template: which values the benchmark substitutes into it,
 * whether the text still contains them, and how one is written.
 *
 * `PUT /api/prompts/{benchmark}/{name}` refuses a template that has dropped a
 * required value, because a run would otherwise reach the agent with the code to
 * refactor missing from its prompt. The same rule is applied here so the editor
 * marks the value while it is being edited, and the same placeholder form is
 * used for showing a value and for inserting one.
 */

import type { PromptVariable } from './types';

export type TemplateSyntax = 'format' | 'jinja' | '';

/** How a value is written in this template. */
export function placeholderFor(syntax: string, name: string): string {
  return syntax === 'format' ? `{${name}}` : `{{ ${name} }}`;
}

/** The bracket pair itself, as the label for the template's syntax. */
export function syntaxGlyph(syntax: string): string {
  if (syntax === 'format') return '{ }';
  if (syntax === 'jinja') return '{{ }}';
  return '';
}

export function syntaxTitle(syntax: string): string {
  if (syntax === 'format') return 'Values replace {name} placeholders';
  if (syntax === 'jinja') return 'Rendered with Jinja: {{ expression }}';
  return 'This benchmark declares no template syntax';
}

/** Mirrors the server's presence test, so the editor and the save agree. */
export function isPresent(content: string, syntax: string, name: string): boolean {
  return syntax === 'format' ? content.includes(`{${name}}`) : content.includes(name);
}

export type VariableState = 'present' | 'missing' | 'unused';

export interface VariableRow {
  name: string;
  summary: string;
  required: boolean;
  state: VariableState;
  placeholder: string;
}

export function variableRows(content: string, syntax: string, variables: PromptVariable[]): VariableRow[] {
  return variables.map((variable) => {
    const present = isPresent(content, syntax, variable.name);
    return {
      name: variable.name,
      summary: variable.summary,
      required: variable.required,
      state: present ? 'present' : variable.required ? 'missing' : 'unused',
      placeholder: placeholderFor(syntax, variable.name),
    };
  });
}

/** Required values the text no longer contains. A save with any of these is
 *  refused by the server, so the editor blocks it first. */
export function missingRequired(rows: VariableRow[]): string[] {
  return rows.filter((row) => row.state === 'missing').map((row) => row.name);
}

/** Text with `token` put at the caret, and where the caret belongs afterwards. */
export function insertToken(text: string, start: number, end: number, token: string): { text: string; caret: number } {
  const at = Math.max(0, Math.min(start, text.length));
  const to = Math.max(at, Math.min(end, text.length));
  return { text: `${text.slice(0, at)}${token}${text.slice(to)}`, caret: at + token.length };
}
