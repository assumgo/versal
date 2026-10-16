import { request } from './client';
import { queryString, type Flag, type ListQuery, type Page } from './accounting';
export type Rubric = { id: number; company_id: number | null; codigo: string | null; descricao: string | null; tipo: string | null; conta_debito: string | null; conta_credito: string | null; historico_id: string | null; historico: string | null; status: string | null; debito_gera_cc: number | null; debito_gera_cor: number | null; credito_gera_cc: number | null; credito_gera_cor: number | null };
export type RubricInput = { codigo: string; descricao: string; tipo: 'P' | 'D' | 'E'; conta_debito: string; conta_credito: string; historico_id: string; historico: string; status: 'Ativa' | 'Inativa'; debito_gera_cc: Flag; debito_gera_cor: Flag; credito_gera_cc: Flag; credito_gera_cor: Flag };
const path = (company: number) => `/companies/${company}/rubrics`;
export const rubrics = {
  list: (company: number, query: ListQuery & { status?: string }) => request<Page<Rubric>>(`${path(company)}?${queryString(query)}`),
  read: (company: number, id: number) => request<Rubric>(`${path(company)}/${id}`),
  create: (company: number, input: RubricInput) => request<Rubric>(path(company), { method: 'POST', body: JSON.stringify(input) }),
  update: (company: number, id: number, input: Partial<RubricInput>) => request<Rubric>(`${path(company)}/${id}`, { method: 'PATCH', body: JSON.stringify(input) }),
};
