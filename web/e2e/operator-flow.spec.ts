import { expect, test, type Page } from '@playwright/test';


const MODEL_RESPONSE = {
  models: [{ id: 'stub-model', name: 'Stub model', contextLength: 4096, free: true }],
  source: 'fixture',
};


test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => sessionStorage.setItem('rp-unlocked', '1'));
});


/** Drive the wizard to a queued run and return its id. The two fixture task
 *  titles share no words, so matching on one selects exactly one row. */
async function launch(page: Page, taskTitle: string, timeoutSeconds: number): Promise<string> {
  await page.route('**/api/models', (route) => route.fulfill({ json: MODEL_RESPONSE }));
  await page.goto('/');
  await page.getByRole('button', { name: 'New run' }).first().click();
  await page.getByRole('button', { name: /Fixture Benchmark/ }).click();
  await page.locator('label').filter({ hasText: taskTitle })
    .locator('input[type="checkbox"]').check();
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await page.getByRole('button', { name: /Stub Agent/ }).click();
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await page.getByRole('radio').first().check();
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await page.getByRole('spinbutton').fill(String(timeoutSeconds));

  const created = page.waitForResponse((response) => (
    response.url().endsWith('/api/runs')
    && response.request().method() === 'POST'
    && response.status() === 201
  ));
  await page.getByRole('button', { name: 'Launch' }).click();
  return ((await (await created).json()) as { id: string }).id;
}


test('launches, observes, exports, imports, and recognizes an archived run', async ({ page }, testInfo) => {
  const runId = await launch(page, 'Append a line', 30);

  await page.goto(`/runs/${runId}`);
  await expect(page.getByText('completed', { exact: true })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText('/ 1 passed', { exact: false })).toBeVisible();

  await page.getByRole('button', { name: 'Terminal' }).click();
  await expect(page.locator('.xterm-rows')).toContainText('[stub]', { timeout: 15_000 });

  const zipPath = testInfo.outputPath('run.zip');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export ZIP' }).click();
  const download = await downloadPromise;
  await download.saveAs(zipPath);
  expect((await download.createReadStream()) !== null).toBeTruthy();

  await page.goto('/runs');
  const importedResponse = page.waitForResponse((response) => (
    response.url().endsWith('/api/runs/import')
    && response.request().method() === 'POST'
  ));
  await page.locator('input[type="file"]').setInputFiles(zipPath);
  expect((await importedResponse).status()).toBe(201);
  await expect(page.getByText('Study archive — published results.')).toBeVisible();
  await expect(page.getByText('study archive', { exact: true })).toBeVisible();

  const archivedRow = page.getByText('study archive', { exact: true }).locator(
    'xpath=ancestor::div[contains(concat(" ", normalize-space(@class), " "), " group ")][1]',
  );
  await archivedRow.hover();
  await expect(archivedRow.getByRole('button', { name: 'Restart' })).toHaveCount(0);
  await expect(archivedRow.getByRole('button', { name: 'Delete' })).toBeVisible();
});


test('renders reset raw turn ids as independent chronological disclosures', async ({ page }) => {
  const runId = '00000000000000000000000000000001';
  const sessionId = '00000000000000000000000000000002';
  const timestamp = '2026-01-01T00:00:00Z';
  const run = {
    id: runId,
    status: 'completed',
    benchmark: { key: 'fixture', name: 'Fixture', language: 'python' },
    setup: { key: 's1', name: 'Single agent' },
    agentTool: { key: 'stub', name: 'Stub Agent' },
    model: 'stub-model',
    taskTimeoutSeconds: 30,
    counts: { total: 1, passed: 1, failed: 0, timedOut: 0, pending: 0 },
    passRate: 1,
    queuedAt: timestamp,
    startedAt: timestamp,
    finishedAt: timestamp,
    tasks: [{
      id: '00000000000000000000000000000003',
      taskKey: 'fixture-task',
      title: 'Fixture task',
      ordinal: 0,
      status: 'passed',
      timeoutSeconds: 30,
      startedAt: timestamp,
      finishedAt: timestamp,
      params: {},
      artifacts: [],
      result: {
        passed: true,
        reason: 'passed',
        durationSeconds: 1,
        agentSeconds: 1,
        evaluateSeconds: 0,
        tokensInput: 0,
        tokensOutput: 0,
        model: 'stub-model',
        metrics: {},
        details: {},
      },
      session: {
        id: sessionId,
        role: 'primary',
        status: 'ended',
        startedAt: timestamp,
        finishedAt: timestamp,
        artifacts: [],
      },
    }],
  };
  const events = [
    { type: 'session.start', timestamp, data: { selectedModel: 'stub-model' } },
    { type: 'assistant.turn_start', timestamp, data: { turnId: 0 } },
    { type: 'assistant.message', timestamp, data: { turnId: 0, content: 'first turn output' } },
    { type: 'assistant.turn_end', timestamp, data: { turnId: 0 } },
    { type: 'assistant.turn_start', timestamp, data: { turnId: 0 } },
    { type: 'assistant.message', timestamp, data: { turnId: 0, content: 'second turn output' } },
    { type: 'assistant.turn_end', timestamp, data: { turnId: 0 } },
    { type: 'session.shutdown', timestamp, data: {} },
  ];
  const stream = events.map((event) => `event: event\ndata: ${JSON.stringify(event)}\n\n`).join('')
    + 'event: end\ndata: {}\n\n';

  await page.route(`**/api/runs/${runId}`, (route) => route.fulfill({ json: run }));
  await page.route(`**/api/sessions/${sessionId}/events`, (route) => route.fulfill({
    status: 200,
    contentType: 'text/event-stream',
    headers: { 'Cache-Control': 'no-cache' },
    body: stream,
  }));

  await page.goto(`/runs/${runId}`);
  const turnZero = page.getByRole('button', { name: /Turn 0/ });
  const turnOne = page.getByRole('button', { name: /Turn 1/ });
  await expect(turnZero).toBeVisible();
  await expect(turnOne).toBeVisible();

  await turnZero.click();
  await expect(page.getByText('first turn output')).toBeVisible();
  await expect(page.getByText('second turn output')).toHaveCount(0);
  await turnOne.click();
  await expect(page.getByText('second turn output')).toBeVisible();
});


test('stops a run while its agent is still working', async ({ page }) => {
  // The fixture task sleeps for two minutes, so the run can only end by being
  // stopped. A generous test budget keeps a genuine failure legible.
  test.setTimeout(180_000);
  const runId = await launch(page, 'Slow session', 300);

  await page.goto(`/runs/${runId}`);
  await expect(page.getByText('running', { exact: true })).toBeVisible({ timeout: 60_000 });
  const stop = page.getByRole('button', { name: 'Stop' });
  await expect(stop).toBeVisible();
  await stop.click();

  await expect(page.getByText('stopped', { exact: true })).toBeVisible({ timeout: 60_000 });
  await expect(page.getByRole('button', { name: 'Stop' })).toHaveCount(0);
  // A stopped run is restartable, which is how the operator recovers from it.
  await expect(page.getByRole('button', { name: 'Restart' })).toBeVisible();
});


test('evaluation, plugins and prompts screens describe the shipped pipeline', async ({ page }) => {
  await page.goto('/settings');

  await page.getByRole('button', { name: 'Evaluation & metrics' }).click();
  await expect(page.getByRole('heading', { name: 'Scoring' })).toBeVisible({ timeout: 30_000 });
  // The pipeline in the order it runs.
  for (const stage of ['Can fail a task', 'Recorded', 'Verdict']) {
    await expect(page.getByText(stage, { exact: true })).toBeVisible();
  }
  // The fixture benchmark declares no preparation, so that step is absent
  // rather than shown empty.
  await expect(page.getByText('Prepared by the benchmark', { exact: true })).toHaveCount(0);

  await page.getByRole('button', { name: 'Plugins' }).click();
  // One group per kind of plugin, and no configuration on this screen.
  for (const group of ['Agent tools', 'Benchmarks', 'Metrics', 'Language servers']) {
    await expect(page.getByRole('heading', { name: group, exact: true })).toBeVisible({ timeout: 30_000 });
  }

  await page.getByRole('button', { name: 'Prompts' }).click();
  await expect(page.getByRole('heading', { name: 'Prompt templates' })).toBeVisible({ timeout: 30_000 });
});


test('services screen says what the running deployment was built from', async ({ page }) => {
  await page.goto('/settings');
  await page.getByRole('button', { name: 'Services' }).click();

  // Every row here is a probe: `gradle --version` boots a JVM, and retrieval is
  // asked over the network, so the panel appears when the probes answer.
  await expect(page.getByRole('heading', { name: 'Deployment', exact: true }))
    .toBeVisible({ timeout: 60_000 });
  await expect(page.getByText('Backend', { exact: true })).toBeVisible();
  // the source fingerprint the backend reports for itself
  await expect(page.getByText(/^[0-9a-f]{12}$/).first()).toBeVisible();
  // the dashboard reports its own build, from the dashboard container
  await expect(page.getByText('Dashboard', { exact: true })).toBeVisible();
});


test('runs page remains keyboard reachable at a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/runs');
  await expect(page.getByRole('heading', { name: 'Workflow runs' })).toBeVisible();
  await page.keyboard.press('Tab');
  const activeTag = await page.evaluate(() => document.activeElement?.tagName);
  expect(activeTag).not.toBe('BODY');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});