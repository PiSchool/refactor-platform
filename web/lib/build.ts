/** Identity of the running deployment, as the Services screen reports it.
 *
 *  The backend reports its own build on `/api/system` under the `deployment`
 *  group; the dashboard reports its own on `/rp-build`, which the container
 *  serves from the stamp written when its image was built. Merging the two puts
 *  both halves of a redeploy in one place, so an operator who rebuilt can see
 *  whether either half actually changed.
 */

/** One reported fact about this deployment. `neededBy` says what stops working
 *  without it; `install` is the plugin's own hint for putting it there. */
export interface SystemRow {
  name: string;
  value: string;
  state?: 'ok' | 'absent';
  detail?: string;
  neededBy?: string;
  install?: string;
}

export interface SystemGroup {
  key: string;
  title: string;
  detail: string;
  rows: SystemRow[];
}

export interface SystemReport {
  groups: SystemGroup[];
}

/** What the dashboard image records about itself. `fingerprint` covers the
 *  dashboard source, `buildId` is Next's own identifier for the bundle. */
export interface DashboardBuild {
  fingerprint: string;
  revision: string;
  builtAt: string;
  buildId: string;
}

export function dashboardRow(build: DashboardBuild | null): SystemRow {
  if (!build) {
    return { name: 'Dashboard', value: 'unreported', detail: 'the dashboard did not report a build' };
  }
  const detail = [
    build.fingerprint ? 'source fingerprint' : '',
    build.builtAt ? `built ${build.builtAt}` : 'built outside an image build',
    build.revision ? `revision ${build.revision}` : '',
    build.buildId && build.fingerprint ? `bundle ${build.buildId}` : '',
  ].filter(Boolean).join(' · ');
  return {
    name: 'Dashboard',
    value: build.fingerprint || build.buildId || 'unstamped',
    detail,
  };
}

export function withDashboardRow(groups: SystemGroup[], build: DashboardBuild | null): SystemGroup[] {
  return groups.map((group) => (
    group.key === 'deployment' ? { ...group, rows: [...group.rows, dashboardRow(build)] } : group
  ));
}
