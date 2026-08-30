import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { Checkbox, Chip, Dot, IconBtn, Segmented, Switch } from './controls';

const noop = () => {};

/**
 * These carry state that used to be spelled out in a sentence beside each row.
 * A symbol only replaces that sentence if it is announced, so every control is
 * checked for the name it exposes.
 */
describe('a control announces what it is', () => {
  it('gives a switch its role, its state and its name', () => {
    const markup = renderToStaticMarkup(
      <Switch checked onChange={noop} label="Run the repository test suite" />,
    );
    expect(markup).toContain('role="switch"');
    expect(markup).toContain('aria-checked="true"');
    expect(markup).toContain('aria-label="Run the repository test suite"');
    expect(markup).toContain('title="Run the repository test suite"');
  });

  it('gives an icon button the same name to a screen reader and on hover', () => {
    const markup = renderToStaticMarkup(
      <IconBtn icon={<svg />} label="Restore the default: 900" />,
    );
    expect(markup).toContain('aria-label="Restore the default: 900"');
    expect(markup).toContain('title="Restore the default: 900"');
  });

  it('marks the selected segment, and keeps every alternative visible', () => {
    const markup = renderToStaticMarkup(
      <Segmented<'all' | 'custom'>
        label="How the verdict is decided"
        value="custom"
        onChange={noop}
        options={[{ value: 'all', label: 'Every stage passes' }, { value: 'custom', label: 'Rule' }]} />,
    );
    expect(markup).toContain('role="tablist"');
    expect(markup).toContain('Every stage passes');
    expect(markup).toContain('aria-selected="true"');
    expect(markup.match(/aria-selected="true"/g)).toHaveLength(1);
  });

  it('announces a state marker that is the only statement of that state', () => {
    expect(renderToStaticMarkup(<Dot label="unsaved changes" />)).toContain('aria-label="unsaved changes"');
  });

  it('hides a marker that merely repeats the control around it', () => {
    const markup = renderToStaticMarkup(<Dot />);
    expect(markup).toContain('aria-hidden="true"');
    expect(markup).not.toContain('aria-label');
  });

  it('keeps a multi-selection checkbox native, so range and keyboard behaviour survive', () => {
    const markup = renderToStaticMarkup(
      <Checkbox checked={false} onChange={noop} label="commons-io/TestUtils" />,
    );
    expect(markup).toContain('type="checkbox"');
    expect(markup).toContain('aria-label="commons-io/TestUtils"');
  });
});

describe('a chip states one fact', () => {
  it('puts the longer form on hover, not in the row', () => {
    const markup = renderToStaticMarkup(
      <Chip mono title="Fails the task as test_failed">test_failed</Chip>,
    );
    expect(markup).toContain('title="Fails the task as test_failed"');
    expect(markup).toContain('>test_failed<');
    expect(markup).toContain('font-mono');
  });

  it('is a glyph alone when the tooltip carries the whole statement', () => {
    const markup = renderToStaticMarkup(
      <Chip icon={<svg />} title="Runs inside the task workspace" />,
    );
    expect(markup).toContain('title="Runs inside the task workspace"');
    expect(markup).not.toContain('<span class="truncate">');
  });
});
