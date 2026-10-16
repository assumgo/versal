import { expect, test, type Page } from '@playwright/test';

async function mockCatalogs(page: Page, role = 'Administrador', initialSession = true) {
  let authenticated = initialSession;
  const account = { id: 1, company_id: 1, conta: '00123', descricao: 'Salários', utiliza_cc: 0, tipo_correntista: '9-Nenhum', gera_cor: 0 };
  const accounts = [account, { ...account, id: 2, conta: '00456', descricao: 'Encargos', utiliza_cc: 1, tipo_correntista: '2-Parceiro', gera_cor: 1 }, { ...account, id: 9, company_id: 2, conta: '00999', descricao: 'Conta da outra empresa' }];
  const rows = [{ id: 1, company_id: 1, codigo: '001', descricao: 'Salário mensal', tipo: 'P', conta_debito: '00123', conta_credito: '', historico_id: '001000182', historico: 'Folha de pagamento', status: 'Ativa', debito_gera_cc: 1, debito_gera_cor: 1, credito_gera_cc: 1, credito_gera_cor: 1 }];
  const unexpected: string[] = [];
  await page.route('**/api/v1/**', async route => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace('/api/v1', '');
    if (path === '/auth/refresh') return route.fulfill({ status: authenticated ? 200 : 401, json: authenticated ? { access_token: 'synthetic-test' } : { detail: 'Login necessário' } });
    if (path === '/auth/login') { authenticated = true; return route.fulfill({ json: { access_token: 'synthetic-test' } }); }
    if (path === '/auth/me') return route.fulfill({ json: { id: 1, email: 'synthetic@example.test', role, is_active: true } });
    if (path === '/auth/logout') { authenticated = false; return route.fulfill({ status: 204 }); }
    if (path === '/companies') return route.fulfill({ json: [1, 2].map(id => ({ id, razao: `Empresa ${id}`, fantasia: null, cnpj: null, codigo_siagri: String(id), status: 'Ativa' })) });
    const match = path.match(/^\/companies\/(\d+)\/(chart-accounts|rubrics)(?:\/(\d+))?$/);
    if (!match) { unexpected.push(path); return route.abort(); }
    const company = Number(match[1]), id = Number(match[3]);
    const resource = match[2];
    const collection = resource === 'chart-accounts' ? accounts : rows;
    if (request.method() === 'GET') {
      const q = (url.searchParams.get('q') || '').toLowerCase();
      const exact = url.searchParams.get('conta');
      const status = url.searchParams.get('status');
      let result = collection.filter(row => row.company_id === company) as Array<Record<string, unknown>>;
      if (q) result = result.filter(row => String(row.conta ?? row.codigo ?? '').toLowerCase().includes(q) || String(row.descricao).toLowerCase().includes(q));
      if (exact !== null) result = result.filter(row => row.conta === exact);
      if (status) result = result.filter(row => row.status === status);
      const offset = Number(url.searchParams.get('offset') || 0), limit = Number(url.searchParams.get('limit') || 50);
      return route.fulfill({ json: { items: result.slice(offset, offset + limit), total: result.length, offset, limit } });
    }
    if (!['Administrador', 'Contador'].includes(role)) return route.fulfill({ status: 403, json: { detail: 'Sem permissão' } });
    const body = request.postDataJSON();
    if (resource === 'chart-accounts') {
      if (request.method() === 'POST') {
        const created = { ...account, ...body, id: 3, company_id: company, conta: String(body.conta).replace(/\D/g, ''), gera_cor: body.tipo_correntista.startsWith('2') ? 1 : 0 };
        accounts.push(created);
        return route.fulfill({ status: 201, json: created });
      }
      const found = accounts.find(row => row.id === id && row.company_id === company)!;
      Object.assign(found, body);
      if ('tipo_correntista' in body) found.gera_cor = body.tipo_correntista.startsWith('2') ? 1 : 0;
      return route.fulfill({ json: found });
    }
    const found = request.method() === 'POST' ? { ...rows[0], ...body, id: rows.length + 1, company_id: company } : rows.find(row => row.id === id && row.company_id === company)!;
    Object.assign(found, body);
    for (const side of ['debito', 'credito']) {
      const values = found as Record<string, unknown>;
      const acc = accounts.find(row => row.company_id === company && row.conta === values[`conta_${side}`]);
      if (acc) { values[`${side}_gera_cc`] = acc.utiliza_cc; values[`${side}_gera_cor`] = acc.gera_cor; }
    }
    if (request.method() === 'POST') rows.push(found);
    return route.fulfill({ status: request.method() === 'POST' ? 201 : 200, json: found });
  });
  return unexpected;
}

test('logs in, maintains accounts, and saves rubric flags using the desktop rule', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const unexpected = await mockCatalogs(page, 'Contador', false);
  await page.goto('/plano-de-contas');
  await page.getByLabel('E-mail').fill('synthetic@example.test');
  await page.getByLabel('Senha').fill('synthetic-test-password');
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Plano de contas', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Nova conta' }).click();
  await page.getByLabel('Conta', { exact: true }).fill('007.89');
  await page.getByLabel('Descrição', { exact: true }).fill('Conta sintética criada');
  await page.getByRole('combobox', { name: /^Tipo de correntista/ }).selectOption('2-Parceiro');
  await expect(page.getByText('Gera correntista: Sim', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Salvar', exact: true }).click();
  await expect(page.getByText('00789', { exact: true })).toBeVisible();
  await page.getByLabel('Pesquisar contas').fill('sintética');
  await page.getByRole('button', { name: 'Pesquisar', exact: true }).click();
  await page.getByRole('button', { name: 'Editar conta 3' }).click();
  await page.getByLabel('Descrição', { exact: true }).fill('Conta sintética revisada');
  await page.getByRole('button', { name: 'Salvar', exact: true }).click();
  await expect(page.getByText('Conta sintética revisada', { exact: true })).toBeVisible();
  await page.screenshot({ path: '../docs/screenshots/accounting-plan-desktop.png', fullPage: true });
  await page.getByRole('navigation').getByRole('button', { name: 'Rubricas', exact: true }).click();
  await page.getByRole('button', { name: 'Editar rubrica 1' }).click();
  const debit = page.getByRole('group', { name: 'Débito', exact: true });
  await expect(debit.getByLabel('Gera centro de custo')).toHaveValue('0');
  await expect(debit.getByLabel('Gera centro de custo')).toBeDisabled();
  await expect(debit.getByText(/opções salvas diferem/)).toBeVisible();
  await page.getByLabel('Descrição', { exact: true }).fill('Salário revisado');
  await page.getByRole('region', { name: 'Rubricas cadastradas', exact: true }).evaluate(element => { element.scrollLeft = 0; });
  await page.screenshot({ path: '../docs/screenshots/accounting-rubric-desktop.png', fullPage: true });
  await page.getByRole('button', { name: 'Salvar', exact: true }).click();
  await page.getByRole('button', { name: 'Editar rubrica 1' }).click();
  await expect(debit.getByText(/opções salvas diferem/)).toHaveCount(0);
  const credit = page.getByRole('group', { name: 'Crédito', exact: true });
  await page.getByLabel('Conta crédito', { exact: true }).fill('99999');
  await expect(credit.getByLabel('Gera centro de custo')).toBeEnabled();
  await credit.getByLabel('Gera centro de custo').selectOption('0');
  await page.getByRole('button', { name: 'Salvar', exact: true }).click();
  await page.getByRole('button', { name: 'Editar rubrica 1' }).click();
  await expect(credit.getByLabel('Gera centro de custo')).toHaveValue('0');
  await page.getByRole('button', { name: 'Cancelar', exact: true }).click();
  await page.getByLabel('Empresa ativa').selectOption('2');
  await expect(page.getByText('Nenhum registro encontrado.')).toBeVisible();
  expect(unexpected).toEqual([]);
});

for (const role of ['Operador', 'Consulta']) {
  test(`${role} consults both catalogs without mutation controls`, async ({ page }) => {
    const unexpected = await mockCatalogs(page, role);
    await page.goto('/plano-de-contas');
    await expect(page.getByText('Salários', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Nova conta' })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Editar conta 1' })).toHaveCount(0);
    await page.goto('/rubricas');
    await expect(page.getByText('Salário mensal', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Nova rubrica' })).toHaveCount(0);
    expect(unexpected).toEqual([]);
  });
}

test('mobile catalogs and rubric form remain usable without overflowing the page', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const unexpected = await mockCatalogs(page);
  await page.goto('/plano-de-contas');
  await expect(page.getByText('Salários', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '../docs/screenshots/accounting-plan-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'Abrir menu' }).click();
  await page.getByRole('navigation').getByRole('button', { name: 'Rubricas', exact: true }).click();
  const table = page.getByRole('region', { name: 'Rubricas cadastradas', exact: true });
  expect(await table.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
  await table.evaluate(element => { element.scrollLeft = element.scrollWidth; });
  await expect(page.getByRole('columnheader', { name: 'Status', exact: true })).toBeInViewport();
  await page.getByRole('button', { name: 'Editar rubrica 1' }).click();
  await expect(page.getByRole('heading', { name: 'Editar rubrica', exact: true })).toBeVisible();
  await expect(page.getByRole('group', { name: 'Débito', exact: true }).getByLabel('Gera centro de custo')).toHaveValue('0');
  await table.evaluate(element => { element.scrollLeft = 0; });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '../docs/screenshots/accounting-rubric-mobile.png', fullPage: true });
  expect(unexpected).toEqual([]);
});
