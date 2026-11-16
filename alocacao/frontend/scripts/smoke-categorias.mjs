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

await page.getByRole('button', { name: 'Cadastros' }).click().catch(() => undefined);
await page.getByRole('link', { name: 'Categorias' }).click();
await page.getByRole('heading', { name: 'Categorias', exact: true }).waitFor();
await page.waitForTimeout(500);

const expected = ['Notebook', 'Monitor', 'Periféricos', 'Rede', 'Desktop', 'Servidor'];
for (const nome of expected) {
  await page.getByRole('cell', { name: nome, exact: true }).waitFor();
}

await page.screenshot({ path: path.join(outDir, 'cadastros-categorias.png'), fullPage: true });

const unique = `Categoria Smoke ${Date.now()}`;
await page.getByLabel('Nome').fill(unique);
await page.getByLabel('Descrição').fill('Criada pelo smoke test');
await page.getByRole('button', { name: 'Criar categoria' }).click();
await page.getByText('Categoria criada.').waitFor();
await page.getByRole('cell', { name: unique, exact: true }).waitFor();

await page.getByRole('row', { name: new RegExp(unique) }).getByRole('button', { name: 'Editar' }).click();
await page.getByLabel('Descrição').fill('Atualizada pelo smoke test');
await page.getByRole('button', { name: 'Salvar alterações' }).click();
await page.getByText('Categoria atualizada.').waitFor();

page.once('dialog', (dialog) => dialog.accept());
await page.getByRole('row', { name: new RegExp(unique) }).getByRole('button', { name: 'Excluir' }).click();
await page.getByText('Categoria excluída.').waitFor();

await page.screenshot({ path: path.join(outDir, 'cadastros-categorias-apos-crud.png'), fullPage: true });
console.log(JSON.stringify({ ok: true, seeded: expected }, null, 2));
await browser.close();
