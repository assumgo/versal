import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';

const outDir = '/opt/cursor/artifacts';
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

async function ensureLogin() {
  await page.goto('http://localhost:5174/login', { waitUntil: 'networkidle' });
  const localLogin = page.getByRole('button', { name: 'Entrar localmente' });
  if (await localLogin.isVisible().catch(() => false)) {
    await localLogin.click();
    await page.waitForURL('**/');
  }
}

await ensureLogin();

await page.getByRole('button', { name: 'Cadastros' }).click();
for (const label of ['Categorias', 'Colaboradores', 'Fornecedores']) {
  await page.getByRole('link', { name: label }).waitFor();
}

await page.getByRole('link', { name: 'Colaboradores' }).click();
await page.getByRole('heading', { name: 'Colaboradores', exact: true }).waitFor();
const collabName = `Colaborador Smoke ${Date.now()}`;
await page.getByLabel('Nome', { exact: true }).fill(collabName);
await page.getByLabel('E-mail pessoal').fill(`smoke${Date.now()}@example.com`);
await page.getByLabel('CPF').fill('529.982.247-25');
await page.getByLabel('Data de nascimento').fill('1992-08-20');
await page.getByLabel('Número celular').fill('(11) 91234-5678');
await page.getByRole('button', { name: 'Criar colaborador' }).click();
await page.getByText('Colaborador criado.').waitFor();
await page.screenshot({ path: path.join(outDir, 'cadastros-colaboradores.png'), fullPage: true });

page.once('dialog', (dialog) => dialog.accept());
await page.getByRole('row', { name: new RegExp(collabName) }).getByRole('button', { name: 'Excluir' }).click();
await page.getByText('Colaborador excluído.').waitFor();

await page.getByRole('link', { name: 'Fornecedores' }).click();
await page.getByRole('heading', { name: 'Fornecedores', exact: true }).waitFor();
const company = `Fornecedor Smoke ${Date.now()}`;
await page.getByLabel('Razão social').fill(company);
await page.getByLabel('Nome fantasia').fill('Fantasia Smoke');
await page.getByLabel('CNPJ/CPF').fill('11.222.333/0001-81');
await page.getByRole('button', { name: 'Criar fornecedor' }).click();
await page.getByText('Fornecedor criado.').waitFor();
await page.screenshot({ path: path.join(outDir, 'cadastros-fornecedores.png'), fullPage: true });

page.once('dialog', (dialog) => dialog.accept());
await page.getByRole('row', { name: new RegExp(company) }).getByRole('button', { name: 'Excluir' }).click();
await page.getByText('Fornecedor excluído.').waitFor();

await page.getByRole('link', { name: 'Categorias' }).click();
await page.getByRole('heading', { name: 'Categorias', exact: true }).waitFor();
await page.screenshot({ path: path.join(outDir, 'cadastros-submenu-categorias.png'), fullPage: true });

console.log(JSON.stringify({ ok: true }, null, 2));
await browser.close();
