import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { AccountingReview } from '../pages/AccountingReview';
import { setToken } from '../api/client';

const company = { id: 1, razao: 'Empresa A', status: 'Ativa', codigo_siagri: '1', fantasia: null, cnpj: null };
const row = { id: 1, competencia: '09/2026', cpf: '001.234', nome: 'Ana Sintética', codigo_verba: '01', verba: 'Salário', valor: '12345678901234567890.123456789', conta_debito: '4211020001', debito_gera_cc: true, debito_gera_cor: true, conta_credito: '00123', credito_gera_cc: false, credito_gera_cor: false, historico_id: '001000182', historico: 'Salário sintético', centro_custo: '0001', correntista: '001234', fonte: 'Extrato' };
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
const page = (items: unknown[] = [row], total = items.length, offset = 0, limit = 50) => ({ items, total, offset, limit });
beforeEach(() => setToken('test-token'));
afterEach(() => { vi.unstubAllGlobals(); setToken(null); });

it('selects latest valid competence and displays desktop columns with exact decimals', async () => {
  const urls: URL[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string) => {
    const url = new URL(input); urls.push(url);
    return response(url.pathname.endsWith('/competences') ? ['09/2026', '08/2026', 'legado'] : page());
  }));
  render(<AccountingReview company={company} />);
  expect(await screen.findByText('Ana Sintética')).toBeVisible();
  expect(screen.getByLabelText('Competência da conferência')).toHaveValue('09/2026');
  expect(screen.getByText('12345678901234567890.123456789')).toBeVisible();
  expect(screen.getAllByRole('columnheader')).toHaveLength(17);
  expect(screen.getAllByText('Sim')).toHaveLength(2);
  expect(screen.getAllByText('Não')).toHaveLength(2);
  expect(urls.at(-1)?.searchParams.get('competence')).toBe('09/2026');
  expect(screen.queryByRole('button', { name: /Salvar|Editar|Excluir/ })).not.toBeInTheDocument();
});

it('changes competence resets pagination and refreshes options and lines', async () => {
  const urls: URL[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string) => {
    const url = new URL(input); urls.push(url);
    return response(url.pathname.endsWith('/competences') ? ['09/2026', '08/2026'] : page([{ ...row, competencia: url.searchParams.get('competence') }], 101, Number(url.searchParams.get('offset') || 0), Number(url.searchParams.get('limit') || 50)));
  }));
  render(<AccountingReview company={company} />);
  await screen.findByText('Ana Sintética');
  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }));
  await waitFor(() => expect(urls.at(-1)?.searchParams.get('offset')).toBe('50'));
  await userEvent.selectOptions(screen.getByLabelText('Competência da conferência'), '08/2026');
  await waitFor(() => expect(urls.at(-1)?.searchParams.get('competence')).toBe('08/2026'));
  expect(urls.at(-1)?.searchParams.get('offset')).toBe('0');
  await userEvent.selectOptions(screen.getByLabelText('Registros por página'), '25');
  await waitFor(() => expect(urls.at(-1)?.searchParams.get('limit')).toBe('25'));
  const before = urls.filter(url => url.pathname.endsWith('/competences')).length;
  await userEvent.click(screen.getByRole('button', { name: 'Atualizar conferência' }));
  await waitFor(() => expect(urls.filter(url => url.pathname.endsWith('/competences')).length).toBe(before + 1));
  expect(screen.getByLabelText('Competência da conferência')).toHaveValue('08/2026');
});

it('handles absent company, empty imports and malformed legacy competence without invalid requests', async () => {
  let values: string[] = [];
  const urls: URL[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string) => { const url = new URL(input); urls.push(url); return response(url.pathname.endsWith('/competences') ? values : page([])); }));
  const view = render(<AccountingReview company={null} />);
  expect(screen.getByText('Selecione uma empresa.')).toBeVisible();
  view.rerender(<AccountingReview company={company} />);
  expect(await screen.findByText('Nenhuma competência importada.')).toBeVisible();
  values = ['legado'];
  await userEvent.click(screen.getByRole('button', { name: 'Atualizar conferência' }));
  expect(await screen.findByText(/Selecione uma competência válida/)).toBeVisible();
  expect(urls.every(url => url.pathname.endsWith('/competences'))).toBe(true);
});

it('retries failed competence and movement consultations', async () => {
  let failCompetences = true, failLines = true;
  vi.stubGlobal('fetch', vi.fn(async (input: string) => {
    if (input.endsWith('/competences')) {
      if (failCompetences) { failCompetences = false; throw new Error('Sem competências'); }
      return response(['09/2026']);
    }
    if (failLines) { failLines = false; throw new Error('Sem movimentos'); }
    return response(page([]));
  }));
  render(<AccountingReview company={company} />);
  await userEvent.click(await screen.findByRole('button', { name: 'Tentar novamente' }));
  expect(await screen.findByText('Sem movimentos')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }));
  expect(await screen.findByText('Nenhum registro encontrado.')).toBeVisible();
});

it('discards old competence and company responses', async () => {
  const deferred: ((value: Response) => void)[] = [];
  vi.stubGlobal('fetch', vi.fn((input: string) => {
    if (input.endsWith('/competences')) return Promise.resolve(response(['09/2026', '08/2026']));
    if (input.includes('/companies/1/')) return new Promise<Response>(resolve => { deferred.push(resolve); });
    return Promise.resolve(response(page([{ ...row, nome: 'Empresa B' }])));
  }));
  const view = render(<AccountingReview company={company} />);
  await waitFor(() => expect(deferred).toHaveLength(1));
  await userEvent.selectOptions(screen.getByLabelText('Competência da conferência'), '08/2026');
  await waitFor(() => expect(deferred).toHaveLength(2));
  await act(async () => { deferred[1](response(page([{ ...row, nome: 'Agosto' }]))); });
  await screen.findByText('Agosto');
  await act(async () => { deferred[0](response(page())); });
  expect(screen.queryByText('Ana Sintética')).not.toBeInTheDocument();
  view.rerender(<AccountingReview company={{ ...company, id: 2 }} />);
  expect(await screen.findByText('Empresa B', { selector: 'td' })).toBeVisible();
  expect(screen.queryByText('Agosto')).not.toBeInTheDocument();
});
