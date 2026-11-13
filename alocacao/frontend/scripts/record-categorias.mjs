import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';

const outDir = '/opt/cursor/artifacts';
const videoDir = path.join(outDir, 'playwright-video-categorias');
fs.mkdirSync(videoDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: videoDir, size: { width: 1440, height: 900 } },
});
const page = await context.newPage();

await page.goto('http://localhost:5174/login', { waitUntil: 'networkidle' });
const localLogin = page.getByRole('button', { name: 'Entrar localmente' });
if (await localLogin.isVisible().catch(() => false)) {
  await localLogin.click();
  await page.waitForURL('**/');
}
await page.waitForTimeout(600);
await page.getByRole('link', { name: 'Cadastros' }).click();
await page.getByRole('heading', { name: 'Categorias', exact: true }).waitFor();
await page.waitForTimeout(900);

const unique = `Impressora Demo ${Date.now()}`;
await page.getByLabel('Nome').fill(unique);
await page.getByLabel('Descrição').fill('Demo UI');
await page.waitForTimeout(400);
await page.getByRole('button', { name: 'Criar categoria' }).click();
await page.getByText('Categoria criada.').waitFor();
await page.waitForTimeout(700);

await page.getByRole('row', { name: new RegExp(unique) }).getByRole('button', { name: 'Editar' }).click();
await page.getByLabel('Descrição').fill('Atualizada');
await page.waitForTimeout(400);
await page.getByRole('button', { name: 'Salvar alterações' }).click();
await page.getByText('Categoria atualizada.').waitFor();
await page.waitForTimeout(700);

page.once('dialog', (dialog) => dialog.accept());
await page.getByRole('row', { name: new RegExp(unique) }).getByRole('button', { name: 'Excluir' }).click();
await page.getByText('Categoria excluída.').waitFor();
await page.waitForTimeout(1000);

await context.close();
await browser.close();

const videos = fs.readdirSync(videoDir).filter((f) => f.endsWith('.webm'));
const src = path.join(videoDir, videos[0]);
const destWebm = path.join(outDir, 'categorias-crud-demo.webm');
fs.renameSync(src, destWebm);
console.log(destWebm);
