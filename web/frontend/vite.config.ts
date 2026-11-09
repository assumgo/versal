import fs from 'node:fs';
import { defineConfig, type UserConfig } from 'vitest/config';

function devServer(): UserConfig['server'] {
  const certPath = process.env.VITE_SSL_CERT;
  const keyPath = process.env.VITE_SSL_KEY;
  if (!certPath || !keyPath) return undefined;
  return {
    https: {
      cert: fs.readFileSync(certPath),
      key: fs.readFileSync(keyPath),
    },
  };
}

export default defineConfig({
  server: devServer(),
  test: {
    environment: 'jsdom',
    // Keep DOM interactions reliable on shared development/CI machines.
    maxWorkers: 2,
    testTimeout: 15000,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.tsx'],
  },
});
