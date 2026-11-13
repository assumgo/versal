import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';

const outDir = '/opt/cursor/artifacts';
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto('http://localhost:5174/login', { waitUntil: 'networkidle' });
const localLogin = page.getByRole('button', { name: 'Entrar localmente' });
if (await localLogin.isVisible().catch(() => false)) {
  await localLogin.click();
  await page.waitForURL('**/');
}

await page.getByRole('link', { name: 'Equipamentos' }).click();
await page.getByRole('heading', { name: 'Equipamentos', exact: true }).waitFor();
await page.getByText('Selecione os filtros e clique em Pesquisar').waitFor();
await page.screenshot({ path: path.join(outDir, 'equipamentos-vazio.png'), fullPage: true });

await page.getByRole('button', { name: '+ Novo equipamento' }).click();
await page.getByRole('heading', { name: 'Novo equipamento' }).waitFor();

const stamp = Date.now();
const form = page.locator('.equipamento-form');
await form.getByLabel('Descrição').fill(`Notebook Smoke ${stamp}`);
await form.getByLabel('Marca').fill('Dell');
await form.getByLabel('Modelo').fill('Latitude 5440');
await form.getByLabel('Número de série').fill(`SN-${stamp}`);
await form.getByLabel('Número patrimônio').fill(`PAT-${stamp}`);
await form.getByLabel('MAC Address').fill('AA:BB:CC:DD:EE:01');
await form.getByLabel('Categoria').selectOption({ label: 'Notebook' });
await form.getByRole('button', { name: 'Incluir equipamento' }).click();
await page.getByText('Equipamento criado.').waitFor();

const filters = page.locator('.filters-panel');
await filters.getByLabel('Categoria').selectOption({ label: 'Todas' });
await filters.getByLabel('Status').selectOption({ label: 'Disponível' });
await page.getByRole('button', { name: 'Pesquisar' }).click();
await page.getByRole('cell', { name: `Notebook Smoke ${stamp}` }).waitFor();
await page.screenshot({ path: path.join(outDir, 'equipamentos-grid.png'), fullPage: true });

await page.getByRole('row', { name: new RegExp(`Notebook Smoke ${stamp}`) }).getByRole('button', { name: 'Editar' }).click();
await page.getByRole('heading', { name: /Editar equipamento/ }).waitFor();
await page.locator('.equipamento-form').getByLabel('Descrição').fill(`Notebook Smoke Edit ${stamp}`);
await page.getByRole('button', { name: 'Salvar alterações' }).click();
await page.getByText('Equipamento atualizado.').waitFor();
await page.getByRole('button', { name: 'Pesquisar' }).click();
await page.getByRole('cell', { name: `Notebook Smoke Edit ${stamp}` }).waitFor();

page.once('dialog', (dialog) => dialog.accept());
await page
  .getByRole('row', { name: new RegExp(`Notebook Smoke Edit ${stamp}`) })
  .getByRole('button', { name: 'Excluir' })
  .click();
await page.getByText('Equipamento excluído.').waitFor();

console.log(JSON.stringify({ ok: true }, null, 2));
await browser.close();
