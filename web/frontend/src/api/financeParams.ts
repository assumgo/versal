import { request } from './client';
import { queryString, type Page } from './accounting';

export type FinanceParamInput = { tipo: string; documento_id: string; parceiro_cpf_cnpj: string; codigo_parceiro_siagri: string; conta_contrapartida: string; centro_custo: string; vencimento_dia: number; historico: string };
export type FinanceParam = { id: number; company_id: number | null; tipo: string | null; documento_id: string | null; parceiro_cpf_cnpj: string | null; codigo_parceiro_siagri: string | null; conta_contrapartida: string | null; centro_custo: string | null; vencimento_dia: number | null; historico: string | null; ativo: number | null };
const path = (company: number) => `/companies/${company}/finance-params`;
export const financeParams = {
  list: (company: number, query: { offset?: number; limit?: number }) => request<Page<FinanceParam>>(`${path(company)}?${queryString(query)}`),
  create: (company: number, input: FinanceParamInput) => request<FinanceParam>(path(company), { method: 'POST', body: JSON.stringify(input) }),
};
