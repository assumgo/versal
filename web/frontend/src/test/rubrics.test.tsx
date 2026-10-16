import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { Rubrics } from '../pages/Rubrics';
import { setToken } from '../api/client';

const company = { id: 1, razao: 'Empresa A', status: 'Ativa', codigo_siagri: '1', fantasia: null, cnpj: null };
const rubric = { id: 1, company_id: 1, codigo: '001', descricao: 'Salário', tipo: 'E', conta_debito: '001', conta_credito: '', historico_id: '001000182', historico: 'h'.repeat(250), status: 'Ativa', debito_gera_cc: 1, debito_gera_cor: 1, credito_gera_cc: 1, credito_gera_cor: 1 };
const account = { id: 1, company_id: 1, conta: '001', descricao: 'Conta salarial', utiliza_cc: 0, tipo_correntista: '9-Nenhum', gera_cor: 0 };
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });
const page = (items: unknown[], total = items.length) => ({ items, total, offset: 0, limit: 50 });
beforeEach(() => setToken('test-token'));
afterEach(() => { vi.unstubAllGlobals(); setToken(null); });

it('preserves desktop save rules and leaves untouched legacy fields out of PATCH', async () => {
  let body: Record<string, unknown> | null = null;
  vi.stubGlobal('fetch', vi.fn(async (input: string, init?: RequestInit) => {
    if (input.includes('chart-accounts')) return response(page([account]));
    if (init?.method === 'PATCH') { body = JSON.parse(String(init.body)); return response({ ...rubric, descricao: 'Atualizada', debito_gera_cc: 0, debito_gera_cor: 0 }); }
    return response(page([rubric]));
  }));
  render(<Rubrics company={company} canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Editar rubrica 1' }));
  expect(screen.getByLabelText('Tipo da rubrica')).toHaveValue('E');
  expect(screen.getByLabelText('Histórico')).toHaveValue('h'.repeat(250));
  const debit = screen.getByRole('group', { name: 'Débito' });
  await waitFor(() => expect(within(debit).getByLabelText('Gera centro de custo')).toBeDisabled());
  expect(within(debit).getByLabelText('Gera centro de custo')).toHaveValue('0');
  expect(await screen.findByText(/opções salvas diferem/)).toBeVisible();
  await userEvent.clear(screen.getByLabelText('Descrição'));
  await userEvent.type(screen.getByLabelText('Descrição'), 'Atualizada');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  await screen.findByText('Registro salvo.');
  expect(body).toEqual({ descricao: 'Atualizada' });
});

it('creates an incomplete rubric with manual flags when no account exists', async () => {
  let body: Record<string, unknown> | null = null;
  vi.stubGlobal('fetch', vi.fn(async (input: string, init?: RequestInit) => {
    if (input.includes('chart-accounts')) return response(page([]));
    if (init?.method === 'POST') { body = JSON.parse(String(init.body)); return response(rubric, 201); }
    return response(page([]));
  }));
  render(<Rubrics company={company} canWrite />);
  await screen.findByText('Nenhum registro encontrado.');
  await userEvent.click(screen.getByRole('button', { name: 'Nova rubrica' }));
  await userEvent.type(screen.getByLabelText('Código da rubrica'), 'FGTS');
  await userEvent.type(screen.getByLabelText('Descrição'), 'Encargo');
  await userEvent.type(screen.getByLabelText('Conta débito'), '999');
  const debit = screen.getByRole('group', { name: 'Débito' });
  await userEvent.selectOptions(within(debit).getByLabelText('Gera centro de custo'), '0');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  await screen.findByText('Registro salvo.');
  expect(body).toMatchObject({ codigo: 'FGTS', conta_debito: '999', debito_gera_cc: 0, debito_gera_cor: 1 });
});

it('filters status and inactivates without deleting the record', async () => {
  const calls: { url: URL; method: string; body?: unknown }[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string, init?: RequestInit) => {
    if (input.includes('chart-accounts')) return response(page([]));
    calls.push({ url: new URL(input), method: init?.method ?? 'GET', body: init?.body ? JSON.parse(String(init.body)) : undefined });
    return response(init?.method === 'PATCH' ? rubric : page([rubric]));
  }));
  render(<Rubrics company={company} canWrite />);
  await screen.findByText('Salário');
  await userEvent.selectOptions(screen.getByLabelText('Filtrar status'), 'Ativa');
  await waitFor(() => expect(calls.at(-1)?.url.searchParams.get('status')).toBe('Ativa'));
  await userEvent.click(await screen.findByRole('button', { name: 'Editar rubrica 1' }));
  await userEvent.selectOptions(screen.getByLabelText('Status da rubrica'), 'Inativa');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  await screen.findByText('Registro salvo.');
  expect(calls.find(call => call.method === 'PATCH')?.body).toEqual({ status: 'Inativa' });
  expect(calls.some(call => call.method === 'DELETE')).toBe(false);
});

it.each([false, true])('blocks writing for read-only roles or an inactive company (canWrite=%s)', async canWrite => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(response(page([rubric])))));
  render(<Rubrics company={canWrite ? { ...company, status: 'Inativa' } : company} canWrite={canWrite} />);
  await screen.findByText('Salário');
  expect(screen.queryByRole('button', { name: 'Nova rubrica' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Editar rubrica 1' })).not.toBeInTheDocument();
});

it('ignores a successful save after the company changes', async () => {
  let finish!: (value: Response) => void;
  vi.stubGlobal('fetch', vi.fn((input: string, init?: RequestInit) => {
    if (input.includes('chart-accounts')) return Promise.resolve(response(page([])));
    if (init?.method === 'PATCH') return new Promise<Response>(resolve => { finish = resolve; });
    return Promise.resolve(response(page([{ ...rubric, descricao: input.includes('/companies/2/') ? 'Rubrica B' : 'Salário' }])));
  }));
  const view = render(<Rubrics company={company} canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Editar rubrica 1' }));
  await userEvent.type(screen.getByLabelText('Descrição'), ' alterado');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  view.rerender(<Rubrics company={{ ...company, id: 2 }} canWrite />);
  await screen.findByText('Rubrica B');
  await act(async () => { finish(response(rubric)); });
  expect(screen.queryByText('Registro salvo.')).not.toBeInTheDocument();
  expect(screen.queryByLabelText('Descrição')).not.toBeInTheDocument();
});

it('returns to the last valid page when inactivating the final filtered row', async () => {
  let inactivated = false;
  vi.stubGlobal('fetch', vi.fn(async (input: string, init?: RequestInit) => {
    if (input.includes('chart-accounts')) return response(page([]));
    if (init?.method === 'PATCH') { inactivated = true; return response({ ...rubric, status: 'Inativa' }); }
    const url = new URL(input);
    const offset = Number(url.searchParams.get('offset') || 0);
    return response({ items: inactivated && offset >= 50 ? [] : [rubric], total: inactivated ? 50 : 51, offset, limit: 50 });
  }));
  render(<Rubrics company={company} canWrite />);
  await screen.findByText('Salário');
  await userEvent.selectOptions(screen.getByLabelText('Filtrar status'), 'Ativa');
  await screen.findByText('1–50 de 51 registros');
  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }));
  await screen.findByText('51–51 de 51 registros');
  await userEvent.click(screen.getByRole('button', { name: 'Editar rubrica 1' }));
  await userEvent.selectOptions(screen.getByLabelText('Status da rubrica'), 'Inativa');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  expect(await screen.findByText('1–50 de 50 registros')).toBeVisible();
  expect(screen.getByText('Salário')).toBeVisible();
});
