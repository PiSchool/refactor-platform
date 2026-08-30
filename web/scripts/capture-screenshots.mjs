/**
 * Re-capture the dashboard screenshots used in the documentation.
 *
 * Every view is shot twice, once per GitHub appearance, so the docs can embed
 * them in a <picture> and follow the reader's theme. The theme is written to
 * localStorage before the first paint, then verified from the DOM, so nothing
 * is captured mid-flash.
 *
 * Point it at a running stack that already holds real runs:
 *
 *     cd web && node scripts/capture-screenshots.mjs
 *     RP_BASE_URL=http://127.0.0.1:3000 RP_RUN_ID=<id> node scripts/capture-screenshots.mjs
 *     RP_FIGURES_DIR=/repo/docs/figures node /tmp/capture-screenshots.mjs plugins
 *
 * Naming views captures only those, so refreshing one figure leaves the rest
 * of the set untouched:
 *
 *     node scripts/capture-screenshots.mjs plugins settings
 *
 * It only reads: no run is started, restarted or deleted.
 */
import { chromium } from '@playwright/test';
import { mkdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = (process.env.RP_BASE_URL || 'http://127.0.0.1:8787').replace(/\/$/, '');
// RP_FIGURES_DIR lets the tool run from outside the repository — a browser
// container with its own Playwright install, where this file is a copy.
const OUT = process.env.RP_FIGURES_DIR
  ? resolve(process.env.RP_FIGURES_DIR)
  : resolve(dirname(fileURLToPath(import.meta.url)), '..', '..', 'docs', 'figures');
const THEMES = ['light', 'dark'];
const ONLY = new Set(process.argv.slice(2));
const RUN_VIEWS = ['runs', 'run-detail', 'terminal'];
const VIEWPORT = { width: 1440, height: 900 };
const SCALE = 1.5;

/** A run worth showing: executed here, finished, and with something that passed. */
async function pickRun() {
  if (process.env.RP_RUN_ID) return process.env.RP_RUN_ID;
  const response = await fetch(`${BASE}/api/runs`);
  if (!response.ok) throw new Error(`GET /api/runs -> ${response.status}`);
  const { runs } = await response.json();
  const candidate = runs.find(
    (run) =>
      run.status === 'completed' &&
      !(run.config || {}).import &&
      (run.counts || {}).passed > 0 &&
      run.benchmark.key === 'swe',
  ) || runs.find((run) => run.status === 'completed' && (run.counts || {}).passed > 0);
  if (!candidate) throw new Error('no completed run with a passing task to screenshot');
  return candidate.id;
}

async function shot(browser, { name, theme, path, prepare }) {
  if (ONLY.size && !ONLY.has(name)) return;
  const context = await browser.newContext({
    viewport: VIEWPORT,
    deviceScaleFactor: SCALE,
    reducedMotion: 'reduce',
    colorScheme: theme === 'dark' ? 'dark' : 'light',
  });
  await context.addInitScript((value) => {
    window.localStorage.setItem('gh-theme', value);
    window.sessionStorage.setItem('rp-unlocked', '1'); // skip the intro splash
  }, theme);
  const page = await context.newPage();
  try {
    await page.goto(`${BASE}${path}`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(
      (value) => document.documentElement.dataset.theme === value,
      theme,
      { timeout: 15_000 },
    );
    await prepare(page);
    await page.waitForTimeout(700); // let the last transition settle
    const file = join(OUT, `ui-${name}-${theme}.png`);
    await page.screenshot({ path: file });
    console.log(`${`ui-${name}-${theme}.png`.padEnd(30)} ${(statSync(file).size / 1024).toFixed(0)} KB`);
  } finally {
    await context.close();
  }
}

/** Refuse to publish a frame that shows anything shaped like a credential. */
async function assertNoSecrets(page) {
  const suspicious = await page.evaluate(() => {
    const pattern = /(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|[A-Za-z0-9_-]{40,}\.[A-Za-z0-9_-]{20,})/;
    const hits = [];
    for (const input of document.querySelectorAll('input')) {
      if (input.type !== 'password' && pattern.test(input.value || '')) hits.push(input.name || input.id || 'input');
    }
    if (pattern.test(document.body.innerText)) hits.push('body text');
    return hits;
  });
  if (suspicious.length) throw new Error(`possible secret visible on screen: ${suspicious.join(', ')}`);
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const needsRun = !ONLY.size || RUN_VIEWS.some((name) => ONLY.has(name));
  const runId = needsRun ? await pickRun() : '';
  console.log(`base ${BASE}\nrun  ${runId || '(not needed)'}\nout  ${OUT}\n`);

  // Subpixel antialiasing tints small grey text blue, which is visible in a
  // published figure and reads as a defect in the interface. Greyscale
  // antialiasing in a known colour space also makes two captures comparable.
  const browser = await chromium.launch({
    args: ['--disable-lcd-text', '--font-render-hinting=none', '--force-color-profile=srgb'],
  });
  try {
    for (const theme of THEMES) {
      await shot(browser, {
        name: 'runs', theme, path: '/runs',
        prepare: async (page) => {
          await page.getByRole('heading', { name: 'Workflow runs' }).waitFor();
          await page.locator(`a[href="/runs/${runId}"]`).first().waitFor();
        },
      });

      await shot(browser, {
        name: 'run-detail', theme, path: `/runs/${runId}`,
        prepare: async (page) => {
          await page.getByRole('button', { name: 'Agent', exact: true }).click();
          await page.getByRole('button', { name: /^Turn \d+/ }).first().waitFor();
          await page.getByRole('button', { name: /^Turn \d+/ }).first().click();
        },
      });

      await shot(browser, {
        name: 'terminal', theme, path: `/runs/${runId}`,
        prepare: async (page) => {
          await page.getByRole('button', { name: 'Terminal', exact: true }).click();
          await page.locator('.xterm-screen').waitFor({ timeout: 20_000 });
          await page.waitForTimeout(1_500); // replay paints asynchronously
        },
      });

      // Walk benchmark -> tasks -> coding tool, the step that shows the agent,
      // the free-text model field and the provider's live model catalogue.
      await shot(browser, {
        name: 'wizard', theme, path: '/runs/new',
        prepare: async (page) => {
          await page.getByRole('heading', { name: 'New run' }).waitFor();
          await page.getByText('SWE-Refactor', { exact: true }).click(); // advances itself
          await page.getByRole('checkbox').first().waitFor({ timeout: 60_000 });
          await page.getByRole('checkbox').first().check();
          await page.getByRole('button', { name: 'Next' }).click();
          await page.getByText('GitHub Copilot CLI', { exact: true }).click();
          await page.getByPlaceholder('Search models…').waitFor({ timeout: 60_000 });
          await page.waitForTimeout(1_500); // the catalogue arrives from the provider
        },
      });

      await shot(browser, {
        name: 'settings', theme, path: '/settings',
        prepare: async (page) => {
          await page.getByRole('heading', { name: 'Settings' }).waitFor();
          await page.waitForTimeout(1_000);
          await assertNoSecrets(page);
        },
      });

      // Every stage of the verdict with what it measures and the options it
      // accepts, whether the platform, a metric plugin or the benchmark owns it.
      await shot(browser, {
        name: 'evaluation', theme, path: '/settings',
        prepare: async (page) => {
          await page.getByRole('heading', { name: 'Settings' }).waitFor();
          await page.getByRole('button', { name: 'Evaluation & metrics' }).click();
          await page.getByRole('heading', { name: 'Verdict' }).waitFor({ timeout: 30_000 });
          // SWE-Refactor is the only shipped benchmark that uses every part of
          // the pipeline: a preparation step, a recorded score and three gates.
          // Selected by value, and not swallowed: a silent failure here captured
          // a different benchmark and the figure claimed to show something else.
          await page.locator('select').first().selectOption('swe');
          await page.getByText('Workspace changed', { exact: true }).waitFor({ timeout: 30_000 });
          await page.waitForTimeout(700);
          await assertNoSecrets(page);
        },
      });

      // The retrieval pipeline as this deployment runs it: each stage with the
      // model and the candidate count it uses, and whether the active profile
      // departs from the study's.
      await shot(browser, {
        name: 'retrieval', theme, path: '/settings',
        prepare: async (page) => {
          await page.getByRole('heading', { name: 'Settings' }).waitFor();
          await page.getByRole('button', { name: 'Services' }).click();
          await page.getByText('Retrieval', { exact: true }).waitFor({ timeout: 30_000 });
          await page.getByText('Dense search', { exact: true }).waitFor({ timeout: 30_000 });
          await page.getByText('Retrieval', { exact: true }).scrollIntoViewIfNeeded();
          await page.waitForTimeout(700);
          await assertNoSecrets(page);
        },
      });

      // The inventory discovered from plugins/ on this start: each adapter with
      // its declared capabilities, each metric with its namespaced presets.
      await shot(browser, {
        name: 'plugins', theme, path: '/settings',
        prepare: async (page) => {
          await page.getByRole('heading', { name: 'Settings' }).waitFor();
          await page.getByRole('button', { name: 'Plugins' }).click();
          await page.getByText('Agent tools', { exact: true }).waitFor();
          await page.getByText('Metrics', { exact: true }).waitFor();
          await page.waitForTimeout(500);
          await assertNoSecrets(page);
        },
      });
    }
  } finally {
    await browser.close();
  }
}

await main();
