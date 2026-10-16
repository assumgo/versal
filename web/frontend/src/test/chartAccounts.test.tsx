import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { ChartAccounts } from '../pages/ChartAccounts';
import { setToken } from '../api/client';

const company = { id: 1, razao: 'Empresa A', status: 'Ativa', codigo_siagri: '1', fantasia: null, cnpj: null };
const account = { id: 1, company_id: 1, conta: '00123', descricao: 'Salários', utiliza_cc: 1, tipo_correntista: '2-Parceiro', gera_cor: 1 };
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
const page = (items: unknown[] = [account], total = items.length, offset = 0, limit = 50) => ({ items, total, offset, limit });
beforeEach(() => setToken('test-token'));
afterEach(() => { vi.unstubAllGlobals(); setToken(null); });

it('requires a company and offers read-only access for inactive companies', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(page([]))));
  const view = render(<ChartAccounts company={null} canWrite />);
  expect(screen.getByText('Selecione uma empresa.')).toBeVisible();
  view.rerender(<ChartAccounts company={{ ...company, status: 'Inativa' }} canWrite />);
  expect(await screen.findByText('Nenhum registro encontrado.')).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Nova conta' })).not.toBeInTheDocument();
});

it('searches and paginates on the API rather than downloading the entire plan', async () => {
  const calls: URL[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string) => {
    const url = new URL(input); calls.push(url);
    return response(page([account], 1434, Number(url.searchParams.get('offset') || 0), Number(url.searchParams.get('limit') || 50)));
  }));
  render(<ChartAccounts company={company} canWrite />);
  await screen.findByText('Salários');
  expect(calls[0].searchParams.get('limit')).toBe('50');
  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }));
  await waitFor(() => expect(calls.at(-1)?.searchParams.get('offset')).toBe('50'));
  await userEvent.type(screen.getByLabelText('Pesquisar contas'), '100%');
  await userEvent.click(screen.getByRole('button', { name: 'Pesquisar' }));
  await waitFor(() => expect(calls.at(-1)?.searchParams.get('q')).toBe('100%'));
  expect(calls.at(-1)?.searchParams.get('offset')).toBe('0');
  await userEvent.selectOptions(screen.getByLabelText('Registros por página'), '25');
  await waitFor(() => expect(calls.at(-1)?.searchParams.get('limit')).toBe('25'));
});

it('creates an account and displays the actual normalized server result', async () => {
  let created = false;
  let body: Record<string, unknown> | null = null;
  vi.stubGlobal('fetch', vi.fn(async (_input: string, init?: RequestInit) => {
    if (init?.method === 'POST') { body = JSON.parse(String(init.body)); created = true; return response(account, 201); }
    return response(page(created ? [account] : []));
  }));
  render(<ChartAccounts company={company} canWrite />);
  await screen.findByText('Nenhum registro encontrado.');
  await userEvent.click(screen.getByRole('button', { name: 'Nova conta' }));
  await userEvent.type(screen.getByLabelText('Conta'), '00.123');
  await userEvent.type(screen.getByLabelText('Descrição'), 'Salários');
  await userEvent.selectOptions(screen.getByLabelText('Gera centro de custo'), '1');
  await userEvent.clear(screen.getByLabelText('Tipo de correntista'));
  await userEvent.type(screen.getByLabelText('Tipo de correntista'), '2-Parceiro');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  expect(await screen.findByText('Registro salvo.')).toBeVisible();
  expect(await screen.findByText('00123')).toBeVisible();
  expect(body).toMatchObject({ conta: '00.123', descricao: 'Salários', utiliza_cc: 1, tipo_correntista: '2-Parceiro' });
  expect(body).not.toHaveProperty('gera_cor');
});

it('edits only changed fields without replacing a legacy null type or resetting COR', async () => {
  let body: Record<string, unknown> | null = null;
  const legacy = { ...account, tipo_correntista: null };
  vi.stubGlobal('fetch', vi.fn(async (_input: string, init?: RequestInit) => {
    if (init?.method === 'PATCH') { body = JSON.parse(String(init.body)); return response({ ...legacy, descricao: 'Nova' }); }
    return response(page([legacy]));
  }));
  render(<ChartAccounts company={company} canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Editar conta 1' }));
  expect(screen.getByLabelText('Conta')).toBeDisabled();
  await userEvent.clear(screen.getByLabelText('Descrição'));
  await userEvent.type(screen.getByLabelText('Descrição'), 'Nova');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  await screen.findByText('Registro salvo.');
  expect(body).toEqual({ descricao: 'Nova' });
});

it('keeps the form after a conflict and allows retrying a failed consultation', async () => {
  let failed = true;
  vi.stubGlobal('fetch', vi.fn(async (_input: string, init?: RequestInit) => {
    if (init?.method === 'POST') return response({ detail: 'Conta já cadastrada nesta empresa' }, 409);
    if (failed) { failed = false; throw new Error('Falha de conexão'); }
    return response(page([]));
  }));
  render(<ChartAccounts company={company} canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Tentar novamente' }));
  await screen.findByText('Nenhum registro encontrado.');
  await userEvent.click(screen.getByRole('button', { name: 'Nova conta' }));
  await userEvent.type(screen.getByLabelText('Conta'), '00123');
  await userEvent.type(screen.getByLabelText('Descrição'), 'Conta');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  expect(await screen.findByText('Conta já cadastrada nesta empresa')).toBeVisible();
  expect(screen.getByLabelText('Conta')).toHaveValue('00123');
});

it('ignores a list response from the previous company', async () => {
  let finish!: (value: Response) => void;
  vi.stubGlobal('fetch', vi.fn((input: string) => input.includes('/companies/1/')
    ? new Promise<Response>(resolve => { finish = resolve; })
    : Promise.resolve(response(page([{ ...account, company_id: 2, descricao: 'Empresa B conta' }])))));
  const view = render(<ChartAccounts company={company} canWrite />);
  view.rerender(<ChartAccounts company={{ ...company, id: 2 }} canWrite />);
  await screen.findByText('Empresa B conta');
  await act(async () => { finish(response(page())); });
  expect(screen.queryByText('Salários')).not.toBeInTheDocument();
});

it('does not display an old successful save after switching company', async () => {
  let finish!: (value: Response) => void;
  vi.stubGlobal('fetch', vi.fn((input: string, init?: RequestInit) => {
    if (init?.method === 'PATCH') return new Promise<Response>(resolve => { finish = resolve; });
    return Promise.resolve(response(page([{ ...account, descricao: input.includes('/companies/2/') ? 'Empresa B conta' : 'Salários' }])));
  }));
  const view = render(<ChartAccounts company={company} canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Editar conta 1' }));
  await userEvent.type(screen.getByLabelText('Descrição'), ' alterada');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  view.rerender(<ChartAccounts company={{ ...company, id: 2 }} canWrite />);
  await screen.findByText('Empresa B conta');
  await act(async () => { finish(response(account)); });
  expect(screen.queryByText('Registro salvo.')).not.toBeInTheDocument();
  expect(screen.queryByLabelText('Descrição')).not.toBeInTheDocument();
});
