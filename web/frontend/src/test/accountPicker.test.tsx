import { useState } from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { AccountPicker } from '../components/AccountPicker';
import type { ChartAccount } from '../api/chartAccounts';
import { setToken } from '../api/client';

const account = { id: 1, company_id: 1, conta: '001', descricao: 'Salários', utiliza_cc: 0, tipo_correntista: '9-Nenhum', gera_cor: 0 };
const response = (items: unknown[], total = items.length) => new Response(JSON.stringify({ items, total, offset: 0, limit: 25 }), { status: 200 });
function Picker({ company = 1, start = '' }: { company?: number; start?: string }) {
  const [value, setValue] = useState(start);
  const [resolved, setResolved] = useState<ChartAccount | null>(null);
  return <><AccountPicker companyId={company} label="Conta débito" value={value} onChange={setValue} onResolved={setResolved} disabled={false} /><output>{resolved ? `Regra da conta ${resolved.id}` : 'Opções manuais'}</output></>;
}
beforeEach(() => setToken('test-token'));
afterEach(() => { vi.unstubAllGlobals(); setToken(null); });

it('resolves a typed code exactly and keeps unknown accounts available for manual flags', async () => {
  const calls: URL[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string) => {
    const url = new URL(input); calls.push(url);
    return response(url.searchParams.get('conta') === '001' ? [account] : []);
  }));
  render(<Picker />);
  await userEvent.type(screen.getByLabelText('Conta débito'), '0.01');
  expect(await screen.findByText('Regra da conta 1')).toBeVisible();
  expect(calls.at(-1)?.searchParams.get('conta')).toBe('001');
  await userEvent.clear(screen.getByLabelText('Conta débito'));
  await userEvent.type(screen.getByLabelText('Conta débito'), '999');
  expect(await screen.findByText('Opções manuais')).toBeVisible();
  await waitFor(() => expect(calls.at(-1)?.searchParams.get('conta')).toBe('999'));
});

it('searches descriptions with paginated results and selects a real code', async () => {
  const calls: URL[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string) => { const url = new URL(input); calls.push(url); return response([account], 80); }));
  render(<Picker />);
  await userEvent.type(screen.getByLabelText('Conta débito'), 'Salários');
  await userEvent.click(screen.getByRole('button', { name: 'Buscar conta débito' }));
  await userEvent.click(await screen.findByRole('button', { name: 'Selecionar conta 1' }));
  expect(screen.getByLabelText('Conta débito')).toHaveValue('001');
  expect(await screen.findByText('Regra da conta 1')).toBeVisible();
  expect(calls.some(url => url.searchParams.get('q') === 'Salários' && url.searchParams.get('limit') === '25')).toBe(true);
});

it('ignores an exact lookup from the previous company', async () => {
  let finish!: (value: Response) => void;
  vi.stubGlobal('fetch', vi.fn((input: string) => input.includes('/companies/1/') ? new Promise<Response>(resolve => { finish = resolve; }) : Promise.resolve(response([]))));
  const view = render(<Picker company={1} start="001" />);
  await waitFor(() => expect(finish).toBeDefined());
  view.rerender(<Picker company={2} start="001" />);
  await act(async () => { finish(response([account])); });
  expect(screen.queryByText('Regra da conta 1')).not.toBeInTheDocument();
});

it.each([0, null])('uses the canonical lowest-ID rule after selecting an unchanged duplicate code (flag=%s)', async flag => {
  const first = { ...account, utiliza_cc: flag };
  const duplicate = { ...account, id: 2, utiliza_cc: 1, gera_cor: 1 };
  vi.stubGlobal('fetch', vi.fn(async (input: string) => new URL(input).searchParams.has('conta') ? response([first], 2) : response([first, duplicate], 2)));
  function DuplicatePicker() {
    const [value, setValue] = useState('001');
    const [resolved, setResolved] = useState<ChartAccount | null>(null);
    return <><AccountPicker companyId={1} label="Conta débito" value={value} onChange={setValue} onResolved={setResolved} disabled={false} /><output>{resolved ? `Regra canônica ${resolved.id}: ${resolved.utiliza_cc ?? 'inválida'}` : 'Consultando'}</output></>;
  }
  render(<DuplicatePicker />);
  await screen.findByText(`Regra canônica 1: ${flag ?? 'inválida'}`);
  await userEvent.click(screen.getByRole('button', { name: 'Buscar conta débito' }));
  await userEvent.click(await screen.findByRole('button', { name: 'Selecionar conta 2' }));
  await waitFor(() => expect(screen.getByText(`Regra canônica 1: ${flag ?? 'inválida'}`)).toBeVisible());
  expect(screen.queryByText('Regra canônica 2: 1')).not.toBeInTheDocument();
});
