#!/usr/bin/env node
/** Fingerprint of the dashboard source, printed as 12 hex characters.
 *
 *  docker/frontend.Dockerfile records the value in the image, and
 *  scripts/deployment_status.py runs this script over the working tree, so the
 *  two can be compared: equal means the running dashboard was built from the
 *  code on disk.
 *
 *  Only what ends up in the bundle counts. Dependencies, build output, tests and
 *  the tooling that runs them are excluded, so changing a test does not report
 *  the deployment as stale.
 *
 *  Run from the `web` directory.
 */
import { createHash } from 'node:crypto';
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

const SKIP_DIRS = new Set([
  'node_modules', '.next', '.e2e', 'e2e', 'scripts', 'coverage',
  'playwright-report', 'test-results', '.git', '__pycache__', '.pytest_cache',
]);
const SKIP_FILES = new Set([
  'vitest.config.ts', 'playwright.config.ts', 'tsconfig.tsbuildinfo', 'build-stamp',
  '.DS_Store', '.gitignore',
]);
const SKIP_PATTERN = /(\.test\.tsx?|\.spec\.tsx?|\.log)$/;

function walk(dir, into) {
  for (const entry of readdirSync(dir, { withFileTypes: true }).sort((a, b) => (a.name < b.name ? -1 : 1))) {
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) walk(path.join(dir, entry.name), into);
      continue;
    }
    if (!entry.isFile()) continue;
    if (SKIP_FILES.has(entry.name) || SKIP_PATTERN.test(entry.name) || entry.name.startsWith('.env')) continue;
    into.push(path.join(dir, entry.name));
  }
}

const files = [];
walk('.', files);
const digest = createHash('sha256');
for (const file of files.sort()) {
  digest.update(`${path.relative('.', file).split(path.sep).join('/')}\0`);
  digest.update(createHash('sha256').update(readFileSync(file)).digest());
}
process.stdout.write(`${digest.digest('hex').slice(0, 12)}\n`);
