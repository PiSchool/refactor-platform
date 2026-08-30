import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

describe('application metadata assets', () => {
  it('ships a real ICO favicon for the conventional browser request', () => {
    const favicon = join(process.cwd(), 'app', 'favicon.ico');
    expect(existsSync(favicon)).toBe(true);
    expect([...readFileSync(favicon).subarray(0, 4)]).toEqual([0, 0, 1, 0]);
  });
});