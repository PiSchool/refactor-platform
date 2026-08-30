import { describe, expect, it } from 'vitest';
import { dashboardRow, withDashboardRow } from './build';
import type { DashboardBuild, SystemGroup } from './build';

const groups: SystemGroup[] = [
  { key: 'deployment', title: 'Deployment', detail: '', rows: [{ name: 'Backend', value: 'aaaaaaaaaaaa' }] },
  { key: 'agents', title: 'Agent tools', detail: '', rows: [{ name: 'Aider', value: 'aider 0.86.2' }] },
];

const build: DashboardBuild = {
  fingerprint: 'bbbbbbbbbbbb',
  revision: 'abc1234',
  builtAt: '2026-07-26T18:00:00Z',
  buildId: 'iAtCd-cvW_I4',
};

describe('deployment identity', () => {
  it('reports what the dashboard was built from, next to the backend', () => {
    const merged = withDashboardRow(groups, build);
    expect(merged[0].rows.map((r) => r.name)).toEqual(['Backend', 'Dashboard']);
    expect(merged[0].rows[1].value).toBe('bbbbbbbbbbbb');
    expect(merged[0].rows[1].detail).toContain('built 2026-07-26T18:00:00Z');
    expect(merged[0].rows[1].detail).toContain('revision abc1234');
  });

  it('leaves every other group untouched', () => {
    const merged = withDashboardRow(groups, build);
    expect(merged[1]).toBe(groups[1]);
    expect(groups[0].rows).toHaveLength(1);
  });

  it('says the dashboard did not report a build rather than claiming the backend value', () => {
    const row = dashboardRow(null);
    expect(row.value).toBe('unreported');
    expect(row.detail).toContain('did not report');
  });

  it('falls back to the bundle identifier when the image carries no stamp', () => {
    const row = dashboardRow({ fingerprint: '', revision: '', builtAt: '', buildId: 'dev-bundle' });
    expect(row.value).toBe('dev-bundle');
    expect(row.detail).toContain('built outside an image build');
  });
});
