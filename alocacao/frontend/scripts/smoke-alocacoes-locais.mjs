import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';

const outDir = '/opt/cursor/artifacts';
fs.mkdirSync(outDir, { recursive: true });
const API = 'http://127.0.0.1:8001';

async function api(pathname, init) {
  const response = await fetch(`${API}${pathname}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) throw new Error(`${pathname} => ${response.status} ${text}`);
  return data;
}

const stamp = Date.now();
const categorias = await api('/api/categorias');
const categoriaId = categorias.find((item) => item.nome === 'Notebook').id;
const produto = await api('/api/produtos', {
  method: 'POST',
  body: JSON.stringify({
    descricao: `Notebook Aloc ${stamp}`,
    marca: 'Dell',
    modelo: 'Latitude',
    categoria_id: categoriaId,
  }),
});
const equipamento = await api('/api/equipamentos', {
  method: 'POST',
  body: JSON.stringify({
    produto_id: produto.id,
    numero_serie: `SN-AL-${stamp}`,
    numero_patrimonio: `PAT-AL-${stamp}`,
  }),
});
const colaborador = await api('/api/colaboradores', {
  method: 'POST',
  body: JSON.stringify({
    nome: `Colab Aloc ${stamp}`,
    email_pessoal: `aloc.${stamp}@example.com`,
    cpf: `5${String(stamp).slice(-10)}`,
    data_nascimento: '1992-03-10',
    celular: '(62) 97777-3333',
    ativo: true,
  }),
});

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:5174/login', { waitUntil: 'networkidle' });
const localLogin = page.getByRole('button', { name: 'Entrar localmente' });
if (await localLogin.isVisible().catch(() => false)) {
  await localLogin.click();
  await page.waitForURL('**/');
}

await page.getByRole('button', { name: 'Cadastros' }).click();
await page.getByRole('link', { name: 'Locais' }).click();
await page.getByRole('heading', { name: 'Locais', exact: true }).waitFor();
const localForm = page.locator('.cadastro-form');
await localForm.getByRole('textbox', { name: 'Nome', exact: true }).fill(`Local Smoke ${stamp}`);
await localForm.getByLabel('Descrição').fill('Sala de testes');
await localForm.getByRole('button', { name: 'Criar local' }).click();
await page.getByText('Local criado.').waitFor();
await page.getByRole('cell', { name: `Local Smoke ${stamp}` }).waitFor();
await page.screenshot({ path: path.join(outDir, 'cadastros-locais.png'), fullPage: true });

await page.getByRole('link', { name: 'Alocações' }).click();
await page.getByRole('heading', { name: 'Alocações', exact: true }).waitFor();
await page.getByRole('button', { name: '+ Nova alocação' }).click();
const alocForm = page.locator('.equipamento-form');
await alocForm.getByLabel('Tipo').selectOption('entrega');
await alocForm.getByLabel('Destino').selectOption('colaborador');
const equipOption = await alocForm.getByLabel('Equipamento').locator('option').evaluateAll((opts, code) => {
  const match = opts.find((opt) => (opt.textContent || '').includes(code));
  return match ? match.value : '';
}, equipamento.codigo);
if (!equipOption) throw new Error(`Equipamento ${equipamento.codigo} não listado`);
await alocForm.getByLabel('Equipamento').selectOption(equipOption);
await alocForm.getByLabel('Quantidade').fill('1');
await alocForm.getByLabel('Colaborador').selectOption({ label: `Colab Aloc ${stamp}` });
await alocForm.getByRole('button', { name: 'Registrar alocação' }).click();
await page.getByText(/Alocação .* criada/).waitFor();
await page.getByRole('button', { name: 'Ver todos' }).click();
await page.getByText('Entrega').first().waitFor();
await page.screenshot({ path: path.join(outDir, 'alocacoes-form-grid.png'), fullPage: true });

console.log(JSON.stringify({ ok: true, equipamento: equipamento.codigo, colaborador: colaborador.nome }, null, 2));
await browser.close();
