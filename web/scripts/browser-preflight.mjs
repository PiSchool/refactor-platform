// Can Chromium start here?
//
// The browser suite needs a Chromium build and the system libraries it links
// against. Where either is absent the failure is a linker error in the middle of
// a test run, which reads as a broken dashboard. This reports it as one line
// before any test starts.
//
// Exit codes: 0 ready, 3 unavailable (skip), 1 unexpected.
import { chromium } from '@playwright/test';

const firstLine = (text) => String(text ?? '').split('\n').find((line) => line.trim()) ?? '';

try {
  const browser = await chromium.launch();
  await browser.close();
  console.log('browser ready');
  process.exit(0);
} catch (error) {
  const message = firstLine(error?.message);
  const missingBrowser = /Executable doesn't exist|playwright install/i.test(error?.message ?? '');
  const missingLibrary = /error while loading shared libraries|libgbm|libnss3|Host system is missing/i
    .test(error?.message ?? '');
  if (missingBrowser) {
    console.log('browser tests skipped: Chromium is not installed — npx playwright install --with-deps chromium');
    process.exit(3);
  }
  if (missingLibrary) {
    console.log(`browser tests skipped: ${message} — see docs/testing.md for the container route`);
    process.exit(3);
  }
  console.error(`browser preflight failed: ${message}`);
  process.exit(1);
}
