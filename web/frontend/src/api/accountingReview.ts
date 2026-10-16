import { request } from './client';
import { queryString, type Page } from './accounting';

export type AccountingReviewRow = { id: number; competencia: string; cpf: string | null; nome: string | null; codigo_verba: string | null; verba: string | null; valor: string | null; conta_debito: string | null; debito_gera_cc: boolean; debito_gera_cor: boolean; conta_credito: string | null; credito_gera_cc: boolean; credito_gera_cor: boolean; historico_id: string; historico: string | null; centro_custo: string | null; correntista: string; fonte: string | null };
const path = (company: number) => `/companies/${company}`;
export const accountingReview = {
  competences: (company: number) => request<string[]>(`${path(company)}/competences`),
  list: (company: number, query: { competence: string; offset?: number; limit?: number }) => request<Page<AccountingReviewRow>>(`${path(company)}/accounting-review?${queryString(query)}`),
};
