import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { FinanceParams } from '../pages/FinanceParams';
import { setToken } from '../api/client';

const company = { id: 1, razao: 'Empresa A', status: 'Ativa', codigo_siagri: '1', fantasia: null, cnpj: null };
const row = { id: 1, company_id: 1, tipo: 'INSS', documento_id: '0007', parceiro_cpf_cnpj: '001.234', codigo_parceiro_siagri: '0009', conta_contrapartida: '001.23', centro_custo: '001', vencimento_dia: 31, historico: 'Guia sintética', ativo: 1 };
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
const page = (items: unknown[] = [], total = items.length, offset = 0, limit = 50) => ({ items, total, offset, limit });
beforeEach(() => setToken('test-token'));
afterEach(() => { vi.unstubAllGlobals(); setToken(null); });

it('creates a financial parameter without normalizing desktop text', async () => {
  let body: Record<string, unknown> | null = null;
  vi.stubGlobal('fetch', vi.fn(async (_input: string, init?: RequestInit) => {
    if (init?.method === 'POST') { body = JSON.parse(String(init.body)); return response(row, 201); }
    return response(page(body ? [row] : []));
  }));
  render(<FinanceParams company={company} canWrite />);
  await screen.findByText('Nenhum registro encontrado.');
  await userEvent.click(screen.getByRole('button', { name: 'Novo parâmetro' }));
  expect(screen.getByLabelText('Dia vencimento')).toHaveValue(1);
  for (const [label, value] of [['Tipo', ' INSS '], ['ID tipo documento', '0007'], ['CPF/CNPJ parceiro', ' 001.234 '], ['Código parceiro Siagri', '0009'], ['Conta contrapartida', ' 001.23 '], ['Centro custo guia', '001'], ['Histórico', ' Guia sintética ']]) {
    await userEvent.type(screen.getByLabelText(label), value);
  }
  await userEvent.clear(screen.getByLabelText('Dia vencimento'));
  await userEvent.type(screen.getByLabelText('Dia vencimento'), '31');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar parâmetro financeiro' }));
  await screen.findByText('Registro salvo.');
  expect(await screen.findByText('Guia sintética')).toBeVisible();
  expect(body).toEqual({ tipo: ' INSS ', documento_id: '0007', parceiro_cpf_cnpj: ' 001.234 ', codigo_parceiro_siagri: '0009', conta_contrapartida: ' 001.23 ', centro_custo: '001', vencimento_dia: 31, historico: ' Guia sintética ' });
  expect(screen.queryByRole('button', { name: /Editar|Excluir/ })).not.toBeInTheDocument();
});

it('lists legacy values and paginates without downloading all parameters', async () => {
  const urls: URL[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string) => {
    const url = new URL(input); urls.push(url);
    return response(page([{ ...row, historico: null, vencimento_dia: null }], 101, Number(url.searchParams.get('offset') || 0), Number(url.searchParams.get('limit') || 50)));
  }));
  render(<FinanceParams company={company} canWrite={false} />);
  await screen.findByText('INSS');
  expect(screen.getAllByText('—').length).toBe(2);
  expect(screen.queryByRole('button', { name: 'Novo parâmetro' })).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }));
  await waitFor(() => expect(urls.at(-1)?.searchParams.get('offset')).toBe('50'));
  await userEvent.selectOptions(screen.getByLabelText('Registros por página'), '25');
  await waitFor(() => expect(urls.at(-1)?.searchParams.get('limit')).toBe('25'));
  expect(urls.at(-1)?.searchParams.get('offset')).toBe('0');
});

it('requires a company and restricts writing for inactive companies', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => response(page())));
  const view = render(<FinanceParams company={null} canWrite />);
  expect(screen.getByText('Selecione uma empresa.')).toBeVisible();
  view.rerender(<FinanceParams company={{ ...company, status: 'Inativa' }} canWrite />);
  await screen.findByText('Nenhum registro encontrado.');
  expect(screen.queryByRole('button', { name: 'Novo parâmetro' })).not.toBeInTheDocument();
});

it('ignores list and save results after the company changes', async () => {
  let save!: (response: Response) => void;
  let list!: (response: Response) => void;
  let delay = false;
  vi.stubGlobal('fetch', vi.fn((input: string, init?: RequestInit) => {
    if (init?.method === 'POST') return new Promise<Response>(resolve => { save = resolve; });
    if (input.includes('/companies/1/') && delay) return new Promise<Response>(resolve => { list = resolve; });
    return Promise.resolve(response(page()));
  }));
  const view = render(<FinanceParams company={company} canWrite />);
  await screen.findByText('Nenhum registro encontrado.');
  await userEvent.click(screen.getByRole('button', { name: 'Novo parâmetro' }));
  await userEvent.click(screen.getByRole('button', { name: 'Salvar parâmetro financeiro' }));
  expect(screen.getByRole('button', { name: 'Salvar parâmetro financeiro' })).toBeDisabled();
  view.rerender(<FinanceParams company={{ ...company, id: 2 }} canWrite />);
  await act(async () => { save(response(row, 201)); });
  expect(screen.queryByText('Registro salvo.')).not.toBeInTheDocument();
  delay = true;
  view.rerender(<FinanceParams company={company} canWrite />);
  view.rerender(<FinanceParams company={{ ...company, id: 2 }} canWrite />);
  await act(async () => { list(response(page([row]))); });
  expect(screen.queryByText('INSS')).not.toBeInTheDocument();
});

it('keeps the form on save errors and retries failed lists', async () => {
  let failed = true, status = 409;
  vi.stubGlobal('fetch', vi.fn(async (_input: string, init?: RequestInit) => {
    if (init?.method === 'POST') return response({ detail: status === 409 ? 'Empresa inativa' : 'Dia inválido' }, status);
    if (failed) { failed = false; throw new Error('Falha de conexão'); }
    return response(page());
  }));
  render(<FinanceParams company={company} canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Tentar novamente' }));
  await screen.findByText('Nenhum registro encontrado.');
  await userEvent.click(screen.getByRole('button', { name: 'Novo parâmetro' }));
  await userEvent.type(screen.getByLabelText('Tipo'), 'INSS');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar parâmetro financeiro' }));
  expect(await screen.findByText('Empresa inativa')).toBeVisible();
  expect(screen.getByLabelText('Tipo')).toHaveValue('INSS');
  status = 422;
  await userEvent.click(screen.getByRole('button', { name: 'Salvar parâmetro financeiro' }));
  expect(await screen.findByText('Dia inválido')).toBeVisible();
});
