import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';

const outDir = '/opt/cursor/artifacts';
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto('http://localhost:5174/login', { waitUntil: 'networkidle' });
await page.getByRole('button', { name: /Ativar tema escuro/i }).click();
await page.waitForTimeout(300);
await page.screenshot({ path: path.join(outDir, 'login-dark.png'), fullPage: true });
await page.getByRole('button', { name: /Ativar tema claro/i }).click();
await page.waitForTimeout(200);
await page.screenshot({ path: path.join(outDir, 'login-light.png'), fullPage: true });

await page.getByRole('button', { name: 'Entrar localmente' }).click();
await page.waitForURL('**/');
await page.getByRole('heading', { name: 'Resumo do estoque' }).waitFor();
await page.screenshot({ path: path.join(outDir, 'dashboard-light.png'), fullPage: true });

await page.getByRole('button', { name: /Ativar tema escuro/i }).click();
await page.waitForTimeout(300);
const theme = await page.locator('html').getAttribute('data-theme');
if (theme !== 'dark') throw new Error(`Expected dark theme, got ${theme}`);
await page.screenshot({ path: path.join(outDir, 'dashboard-dark.png'), fullPage: true });

const menus = [
  ['Cadastros', 'Cadastros'],
  ['Configurações', 'Configurações'],
  ['Notas Fiscais', 'Notas Fiscais'],
  ['TREs', 'TREs'],
  ['Alocações', 'Alocações'],
  ['Equipamentos', 'Equipamentos'],
];

for (const [link, heading] of menus) {
  await page.getByRole('link', { name: link }).click();
  await page.getByRole('heading', { name: heading }).waitFor();
}

await page.screenshot({ path: path.join(outDir, 'page-equipamentos-dark.png'), fullPage: true });
await page.getByRole('link', { name: 'TREs' }).click();
await page.getByRole('heading', { name: 'TREs' }).waitFor();
await page.screenshot({ path: path.join(outDir, 'page-tres-dark.png'), fullPage: true });

await page.getByRole('button', { name: 'Sair' }).click();
await page.waitForURL('**/login');
await page.getByRole('heading', { name: 'Alocação de Recursos' }).waitFor();

console.log(JSON.stringify({ ok: true, themeAfterToggle: theme, artifacts: fs.readdirSync(outDir) }, null, 2));
await browser.close();
