import { expect, test, type Page } from '@playwright/test';

const review = { id: 1, competencia: '09/2026', cpf: '001.234', nome: 'Ana Sintética', codigo_verba: '01', verba: 'Salário', valor: '1234.56', conta_debito: '4211020001', debito_gera_cc: true, debito_gera_cor: true, conta_credito: '00123', credito_gera_cc: false, credito_gera_cor: false, historico_id: '001000182', historico: 'Folha sintética', centro_custo: '0001', correntista: '001234', fonte: 'Extrato' };
async function mockModules(page: Page, role = 'Contador', initialSession = true) {
  let authenticated = initialSession;
  const financial: Array<Record<string, unknown>> = [];
  const unexpected: string[] = [];
  const writes: Array<Record<string, unknown>> = [];
  await page.route('**/api/v1/**', async route => {
    const req = route.request(), url = new URL(req.url()), path = url.pathname.replace('/api/v1', '');
    if (path === '/auth/refresh') return route.fulfill({ status: authenticated ? 200 : 401, json: authenticated ? { access_token: 'synthetic-test' } : { detail: 'Login necessário' } });
    if (path === '/auth/login') { authenticated = true; return route.fulfill({ json: { access_token: 'synthetic-test' } }); }
    if (path === '/auth/me') return route.fulfill({ json: { id: 1, email: 'synthetic@example.test', role, is_active: true } });
    if (path === '/companies') return route.fulfill({ json: [{ id: 1, razao: 'Empresa sintética', status: 'Ativa', codigo_siagri: '001', fantasia: null, cnpj: null }] });
    if (path === '/companies/1/competences') return route.fulfill({ json: ['09/2026', '08/2026'] });
    if (path === '/companies/1/accounting-review') {
      const items = url.searchParams.get('competence') === '09/2026' ? [review] : [];
      return route.fulfill({ json: { items, total: items.length, offset: 0, limit: 50 } });
    }
    if (path === '/companies/1/finance-params') {
      if (req.method() === 'POST') {
        const body = req.postDataJSON(); writes.push(body);
        const created = { ...body, tipo: body.tipo.trim(), id: financial.length + 1, company_id: 1, ativo: 1 };
        financial.push(created);
        return route.fulfill({ status: 201, json: created });
      }
      return route.fulfill({ json: { items: financial, total: financial.length, offset: 0, limit: 50 } });
    }
    unexpected.push(path); return route.abort();
  });
  return { unexpected, writes };
}

test('logs in, creates a financial parameter and checks imported accounting movements', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const { unexpected, writes } = await mockModules(page, 'Contador', false);
  await page.goto('/parametrizacao-financeira');
  await page.getByLabel('E-mail').fill('synthetic@example.test');
  await page.getByLabel('Senha').fill('synthetic-test-password');
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await page.getByRole('button', { name: 'Novo parâmetro', exact: true }).click();
  for (const [label, value] of [['Tipo', ' INSS '], ['ID tipo documento', '0007'], ['CPF/CNPJ parceiro', '001.234'], ['Código parceiro Siagri', '0009'], ['Conta contrapartida', ' 001.23 '], ['Centro custo guia', '001'], ['Histórico', 'Guia sintética']]) await page.getByLabel(label, { exact: true }).fill(value);
  await page.getByLabel('Dia vencimento', { exact: true }).fill('31');
  await page.screenshot({ path: '../docs/screenshots/finance-params-desktop.png', fullPage: true });
  await page.getByRole('button', { name: 'Salvar parâmetro financeiro', exact: true }).click();
  await expect(page.getByText('Registro salvo.', { exact: true })).toBeVisible();
  expect(writes).toEqual([{ tipo: ' INSS ', documento_id: '0007', parceiro_cpf_cnpj: '001.234', codigo_parceiro_siagri: '0009', conta_contrapartida: ' 001.23 ', centro_custo: '001', vencimento_dia: 31, historico: 'Guia sintética' }]);
  await page.getByRole('navigation').getByRole('button', { name: 'Parametrização Contábil', exact: true }).click();
  await expect(page.getByText('Ana Sintética', { exact: true })).toBeVisible();
  await expect(page.getByRole('columnheader')).toHaveCount(17);
  await page.screenshot({ path: '../docs/screenshots/accounting-review-desktop.png', fullPage: true });
  await page.getByLabel('Competência da conferência', { exact: true }).selectOption('08/2026');
  await expect(page.getByText('Nenhum registro encontrado.', { exact: true })).toBeVisible();
  expect(unexpected).toEqual([]);
});

for (const role of ['Operador', 'Consulta']) test(`${role} reads financial parameters without write controls`, async ({ page }) => {
  const { unexpected, writes } = await mockModules(page, role);
  await page.goto('/parametrizacao-financeira');
  await expect(page.getByRole('heading', { name: 'Parametrização financeira', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Novo parâmetro', exact: true })).toHaveCount(0);
  await page.getByRole('navigation').getByRole('button', { name: 'Parametrização Contábil', exact: true }).click();
  await expect(page.getByText('Ana Sintética', { exact: true })).toBeVisible();
  expect(unexpected).toEqual([]); expect(writes).toEqual([]);
});

test('mobile financial form and accounting table remain within the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const { unexpected } = await mockModules(page);
  await page.goto('/parametrizacao-financeira');
  await page.getByRole('button', { name: 'Novo parâmetro', exact: true }).click();
  await page.screenshot({ path: '../docs/screenshots/finance-params-mobile.png', fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Abrir menu', exact: true }).click();
  await page.getByRole('navigation').getByRole('button', { name: 'Parametrização Contábil', exact: true }).click();
  await expect(page.getByText('Ana Sintética', { exact: true })).toBeVisible();
  const table = page.getByRole('region', { name: 'Conferência contábil', exact: true });
  expect(await table.evaluate(el => el.scrollWidth > el.clientWidth)).toBe(true);
  await page.screenshot({ path: '../docs/screenshots/accounting-review-mobile.png', fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(unexpected).toEqual([]);
});
