import { defineConfig } from '@playwright/test';
const port = Number(process.env.E2E_PORT || 5175);
if (!Number.isInteger(port) || port < 1 || port > 65535 || port === 5174) throw new Error('E2E_PORT deve ser válida e diferente da instância convertida (5174).');
export default defineConfig({
  testDir: './e2e',
  workers: 2,
  use: { baseURL: `http://127.0.0.1:${port}`, launchOptions: { executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome' } },
  webServer: { command: `npm run dev -- --port ${port} --strictPort`, url: `http://127.0.0.1:${port}`, reuseExistingServer: false },
});
