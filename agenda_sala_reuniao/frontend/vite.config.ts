import { defineConfig } from 'vitest/config';

export default defineConfig({
  server: { port: 5174, strictPort: true },
  test: {
    environment: 'jsdom',
    maxWorkers: 2,
    testTimeout: 15000,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
});
