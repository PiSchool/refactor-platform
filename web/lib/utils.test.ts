import { describe, expect, it } from 'vitest';

import { isArchived } from './utils';

describe('archive provenance', () => {
  it('recognizes only current import provenance', () => {
    expect(isArchived({ config: {} })).toBe(false);
    expect(isArchived({ config: { imported: true, source: 'study archive' } })).toBe(false);
    expect(isArchived({
      config: {
        import: {
          format: 'refactor-platform-run',
          sourceRunId: 'source-run',
        },
      },
    })).toBe(true);
  });
});