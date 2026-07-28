import path from 'node:path';

import { defineConfig, devices } from '@playwright/test';

const repository = path.resolve(__dirname, '..');
const externalServers = process.env.PLAYWRIGHT_EXTERNAL_SERVERS === '1';

export default defineConfig({
  testDir: './e2e',
  outputDir: path.join(repository, '.e2e', 'results'),
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'dot' : 'list',
  use: {
    baseURL: 'http://127.0.0.1:13100',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: externalServers ? undefined : [
    {
      name: 'fixture API',
      command: 'uv run python ../scripts/e2e_backend.py',
      cwd: path.join(repository, 'server'),
      url: 'http://127.0.0.1:18100/api/catalog',
      timeout: 120_000,
      reuseExistingServer: false,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      name: 'dashboard',
      command: 'npm run dev -- --hostname 127.0.0.1 --port 13100',
      cwd: path.join(repository, 'web'),
      env: {
        PLATFORM_API_ORIGIN: 'http://127.0.0.1:18100',
      },
      url: 'http://127.0.0.1:13100',
      timeout: 120_000,
      reuseExistingServer: false,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});