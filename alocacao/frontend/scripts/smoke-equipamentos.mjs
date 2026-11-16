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

const stamp = Date.now();
const descricao = `Notebook Smoke ${stamp}`;

await page.getByRole('button', { name: 'Cadastros' }).click();
await page.getByRole('link', { name: 'Produtos' }).click();
await page.getByRole('heading', { name: 'Produtos', exact: true }).waitFor();
await page.getByLabel('Código').waitFor();
await expectReadonlyCodigo(page, 'Gerado automaticamente');
await page.getByLabel('Descrição').fill(descricao);
await page.getByLabel('Marca').fill('Dell');
await page.getByLabel('Modelo').fill('Latitude 5440');
await page.getByLabel('Categoria').selectOption({ label: 'Notebook' });
await page.getByRole('button', { name: 'Criar produto' }).click();
await page.getByText('Produto criado.').waitFor();
await page.getByRole('cell', { name: descricao }).waitFor();
const produtoCodigo = (
  await page.locator('tbody tr').filter({ hasText: descricao }).locator('td').first().innerText()
).trim();
if (!/^\d{6,}$/.test(produtoCodigo)) throw new Error(`Código de produto inesperado: ${produtoCodigo}`);
await page.screenshot({ path: path.join(outDir, 'cadastros-produtos.png'), fullPage: true });

await page.getByRole('link', { name: 'Equipamentos' }).click();
await page.getByRole('heading', { name: 'Equipamentos', exact: true }).waitFor();
await page.getByRole('button', { name: '+ Novo equipamento' }).click();
const form = page.locator('.equipamento-form');
await expectReadonlyCodigo(form, 'Gerado automaticamente');
await form.getByLabel('Produto').selectOption({ label: `${produtoCodigo} — ${descricao}` });
await form.getByLabel('Número de série').fill(`SN-${stamp}`);
await form.getByLabel('Número patrimônio').fill(`PAT-${stamp}`);
await form.getByLabel('MAC Address').fill('AA:BB:CC:DD:EE:02');
await form.getByRole('button', { name: 'Incluir equipamento' }).click();
await page.getByText('Equipamento criado.').waitFor();

const filters = page.locator('.filters-panel');
await filters.getByLabel('Categoria').selectOption({ label: 'Todas' });
await filters.getByLabel('Status').selectOption({ label: 'Disponível' });
await page.getByRole('button', { name: 'Pesquisar' }).click();
await page.getByRole('cell', { name: `PAT-${stamp}` }).waitFor();
const equipamentoCodigo = (
  await page.locator('tbody tr').filter({ hasText: `PAT-${stamp}` }).locator('td').first().innerText()
).trim();
if (!/^1\d{5,}$/.test(equipamentoCodigo) || Number(equipamentoCodigo) < 100000) {
  throw new Error(`Código de equipamento inesperado: ${equipamentoCodigo}`);
}
await page.screenshot({ path: path.join(outDir, 'equipamentos-grid.png'), fullPage: true });

page.once('dialog', (dialog) => dialog.accept());
await page.getByRole('row', { name: new RegExp(`PAT-${stamp}`) }).getByRole('button', { name: 'Excluir' }).click();
await page.getByText('Equipamento excluído.').waitFor();

console.log(
  JSON.stringify({ ok: true, produtoCodigo, equipamentoCodigo }, null, 2),
);
await browser.close();

async function expectReadonlyCodigo(root, expected) {
  const codigo = root.getByLabel('Código');
  const disabled = await codigo.isDisabled();
  const value = await codigo.inputValue();
  if (!disabled) throw new Error('Campo código deveria estar desabilitado');
  if (value !== expected) throw new Error(`Valor inesperado no código: ${value}`);
}
