import { request } from './client';
import { queryString, type Flag, type ListQuery, type Page } from './accounting';
export type ChartAccount = { id: number; company_id: number | null; conta: string | null; descricao: string | null; utiliza_cc: number | null; tipo_correntista: string | null; gera_cor: number | null };
export type ChartAccountInput = { conta: string; descricao: string; utiliza_cc: Flag; tipo_correntista: string };
export type ChartAccountUpdate = Partial<Omit<ChartAccountInput, 'conta'>>;
const path = (company: number) => `/companies/${company}/chart-accounts`;
export const chartAccounts = {
  list: (company: number, query: ListQuery & { conta?: string }) => request<Page<ChartAccount>>(`${path(company)}?${queryString(query)}`),
  read: (company: number, id: number) => request<ChartAccount>(`${path(company)}/${id}`),
  create: (company: number, input: ChartAccountInput) => request<ChartAccount>(path(company), { method: 'POST', body: JSON.stringify(input) }),
  update: (company: number, id: number, input: ChartAccountUpdate) => request<ChartAccount>(`${path(company)}/${id}`, { method: 'PATCH', body: JSON.stringify(input) }),
};
