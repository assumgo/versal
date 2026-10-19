import { expect, test, type Page } from '@playwright/test';
import { resolve } from 'node:path';
import { previewCompany, previewResult } from '../src/test/payrollPreviewFixtures';

const inputPath = resolve('../backend/tests/fixtures/parser_equivalence/extrato_pdf/input.pdf');
async function setup(page: Page, role = 'Operador', login = false) {
  let authenticated = !login;
  const uploads: string[] = [];
  const unexpected: string[] = [];
  let mode: 'ready' | 'blocked' | 'error' = 'ready';
  await page.route('**/api/v1/**', async route => {
    const req = route.request(), path = new URL(req.url()).pathname.replace('/api/v1', '');
    if (path === '/auth/refresh') return route.fulfill({ status: authenticated ? 200 : 401, json: authenticated ? { access_token: 'synthetic' } : { detail: 'Login necessário' } });
    if (path === '/auth/login') { authenticated = true; return route.fulfill({ json: { access_token: 'synthetic' } }); }
    if (path === '/auth/me') return route.fulfill({ json: { id: 1, email: 'synthetic@example.test', role, is_active: true } });
    if (path === '/companies') return route.fulfill({ json: [previewCompany, { ...previewCompany, id: 2, razao: 'Outra empresa sintética' }] });
    if (path === '/companies/1/payroll-import-preview') {
      uploads.push(req.postDataBuffer()?.toString() ?? '');
      if (mode === 'error') return route.fulfill({ status: 400, json: { detail: 'Arquivo ilegível.' } });
      if (mode === 'blocked') return route.fulfill({ json: { ...previewResult, status: 'blocked', issues: [{ code: 'competence_mismatch', severity: 'blocking', message: 'A competência do arquivo difere da selecionada.' }] } });
      return route.fulfill({ json: previewResult });
    }
    unexpected.push(path); return route.abort();
  });
  return { uploads, unexpected, setMode: (value: typeof mode) => { mode = value; } };
}
async function upload(page: Page) {
  await page.getByLabel('Competência ativa', { exact: true }).fill('2026-09');
  await page.getByLabel('Extrato Mensal', { exact: true }).setInputFiles(inputPath);
  await page.getByRole('button', { name: 'Gerar prévia', exact: true }).click();
}

test('logs in and previews a monthly statement with exact totals and duplicate rubrics', async ({ page }) => {
  const mocks = await setup(page, 'Operador', true);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/importacao-folha');
  await page.getByLabel('E-mail').fill('synthetic@example.test');
  await page.getByLabel('Senha').fill('synthetic-password');
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await upload(page);
  await expect(page.getByText('Prévia pronta para conferência.', { exact: true })).toBeVisible();
  await expect(page.getByText(previewResult.summary.net_total, { exact: true })).toBeVisible();
  await expect(page.getByText('SALARIO BASE', { exact: true })).toHaveCount(2);
  expect(mocks.uploads[0]).toContain('name="competence"\r\n\r\n09/2026');
  expect(mocks.uploads[0]).toContain('filename="input.pdf"');
  await page.screenshot({ path: '../docs/screenshots/payroll-preview-desktop.png', fullPage: true });
  expect(mocks.unexpected).toEqual([]);
});

test('shows retry and blocked context results, then clears on competence change', async ({ page }) => {
  const mocks = await setup(page);
  mocks.setMode('error');
  await page.goto('/importacao-folha');
  await upload(page);
  await expect(page.getByText('Arquivo ilegível.', { exact: true })).toBeVisible();
  mocks.setMode('blocked');
  await page.getByRole('button', { name: 'Gerar prévia', exact: true }).click();
  await expect(page.getByText('Prévia bloqueada: confira as divergências.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Ana Sintética', exact: true })).toBeVisible();
  await page.getByLabel('Competência ativa', { exact: true }).fill('2026-10');
  await expect(page.getByText('Prévia bloqueada: confira as divergências.', { exact: true })).toHaveCount(0);
  expect(mocks.unexpected).toEqual([]);
});

test('ignores an old upload response after switching company', async ({ page }) => {
  const mocks = await setup(page);
  let release!: () => void;
  const held = new Promise<void>(done => { release = done; });
  let started!: () => void;
  const requestStarted = new Promise<void>(done => { started = done; });
  await page.route('**/companies/1/payroll-import-preview', async route => {
    started(); await held;
    await route.fulfill({ json: previewResult }).catch(() => {});
  });
  await page.goto('/importacao-folha');
  await upload(page);
  await requestStarted;
  await page.getByLabel('Empresa ativa', { exact: true }).selectOption('2');
  release();
  await expect(page.getByText('Contexto: Outra empresa sintética', { exact: false })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Resultado da prévia', exact: true })).toHaveCount(0);
  expect(mocks.unexpected).toEqual([]);
});

test('Consulta cannot upload documents', async ({ page }) => {
  const mocks = await setup(page, 'Consulta');
  await page.goto('/importacao-folha');
  await expect(page.getByText('Sem permissão para enviar documentos.', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Extrato Mensal', { exact: true })).toHaveCount(0);
  expect(mocks.uploads).toHaveLength(0);
});

test('mobile menu and preview tables preserve viewport width', async ({ page }) => {
  await setup(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Abrir menu', exact: true }).click();
  await page.getByRole('navigation').getByRole('button', { name: 'Importação Folha', exact: true }).click();
  await upload(page);
  await expect(page.getByText('Prévia pronta para conferência.', { exact: true })).toBeVisible();
  const table = page.getByRole('region', { name: 'Colaboradores da prévia', exact: true });
  expect(await table.evaluate(el => el.scrollWidth > el.clientWidth)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '../docs/screenshots/payroll-preview-mobile.png', fullPage: true });
});
