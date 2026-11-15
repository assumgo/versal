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
    descricao: `Notebook TRE UI ${stamp}`,
    marca: 'Dell',
    modelo: 'Latitude',
    categoria_id: categoriaId,
  }),
});
const equipamento = await api('/api/equipamentos', {
  method: 'POST',
  body: JSON.stringify({
    produto_id: produto.id,
    numero_serie: `SN-TRE-${stamp}`,
    numero_patrimonio: `PAT-TRE-${stamp}`,
  }),
});
const colaborador = await api('/api/colaboradores', {
  method: 'POST',
  body: JSON.stringify({
    nome: `Colaborador TRE ${stamp}`,
    email_pessoal: `tre.${stamp}@example.com`,
    cpf: `5${String(stamp).slice(-10)}`,
    data_nascimento: '1991-05-20',
    celular: '(62) 98888-2222',
    ativo: true,
  }),
});
const alocacao = await api('/api/alocacoes', {
  method: 'POST',
  body: JSON.stringify({
    colaborador_id: colaborador.id,
    equipamento_ids: [equipamento.id],
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

await page.getByRole('link', { name: 'TREs' }).click();
await page.getByRole('heading', { name: 'TREs', exact: true }).waitFor();
await page.getByLabel('Nome do colaborador').fill(`Colaborador TRE ${stamp}`);
await page.getByLabel('Código').fill(alocacao.tre_codigo);
await page.getByRole('button', { name: 'Pesquisar' }).click();
await page.getByRole('cell', { name: alocacao.tre_codigo }).waitFor();
await page.getByText('Entrega').first().waitFor();
await page.screenshot({ path: path.join(outDir, 'tres-lista.png'), fullPage: true });

const downloadPromise = page.waitForEvent('download');
await page.getByRole('link', { name: 'Baixar PDF' }).click();
const download = await downloadPromise;
const pdfPath = path.join(outDir, `tre-${alocacao.tre_codigo}.pdf`);
await download.saveAs(pdfPath);

await page.getByRole('link', { name: 'Alocações' }).click();
await page.getByRole('heading', { name: 'Alocações', exact: true }).waitFor();
await page.screenshot({ path: path.join(outDir, 'alocacoes-ativas.png'), fullPage: true });

console.log(
  JSON.stringify(
    {
      ok: true,
      tre_codigo: alocacao.tre_codigo,
      pdf: pdfPath,
      pdf_bytes: fs.statSync(pdfPath).size,
    },
    null,
    2,
  ),
);
await browser.close();
