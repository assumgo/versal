import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';

const outDir = '/opt/cursor/artifacts';
const videoDir = path.join(outDir, 'playwright-video');
fs.mkdirSync(videoDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: videoDir, size: { width: 1440, height: 900 } },
});
const page = await context.newPage();

await page.goto('http://localhost:5174/login', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);
await page.getByRole('button', { name: /Ativar tema escuro/i }).click();
await page.waitForTimeout(900);
await page.getByRole('button', { name: /Ativar tema claro/i }).click();
await page.waitForTimeout(700);
await page.getByRole('button', { name: 'Entrar localmente' }).click();
await page.waitForURL('**/');
await page.waitForTimeout(1000);
await page.getByRole('button', { name: /Ativar tema escuro/i }).click();
await page.waitForTimeout(900);

for (const link of ['Cadastros', 'Notas Fiscais', 'TREs', 'Alocações', 'Equipamentos', 'Dashboard']) {
  await page.getByRole('link', { name: link }).click();
  await page.waitForTimeout(700);
}

await page.getByRole('button', { name: 'Sair' }).click();
await page.waitForURL('**/login');
await page.waitForTimeout(800);

await context.close();
await browser.close();

const videos = fs.readdirSync(videoDir).filter((f) => f.endsWith('.webm'));
if (!videos.length) throw new Error('No video recorded');
const src = path.join(videoDir, videos[0]);
const dest = path.join(outDir, 'alocacao-demo.webm');
fs.renameSync(src, dest);
console.log(dest);
