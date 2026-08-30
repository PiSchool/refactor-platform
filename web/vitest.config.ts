import { fileURLToPath, URL } from 'node:url';

import { configDefaults, defineConfig } from 'vitest/config';

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('.', import.meta.url)),
    },
  },
  oxc: {
    jsx: {
      runtime: 'automatic',
    },
  },
  test: {
    exclude: [...configDefaults.exclude, 'e2e/**'],
  },
});