import { request } from './client';
export type PreviewRubric = { codigo: string; descricao: string; referencia: string; valor: string; tipo: string };
export type PreviewEmployee = { matricula: string; nome: string; cpf: string; situacao: string; cargo: string; centro_custo: string; liquido: string; rubricas: PreviewRubric[] };
export type PayrollPreviewResponse = {
  company_id: number; requested_competence: string; filename: string; size_bytes: number; sha256: string;
  status: 'ready' | 'blocked'; issues: { code: string; severity: 'warning' | 'blocking'; message: string }[];
  summary: { employees: number; rubrics: number; totals_by_type: Record<string, string>; net_total: string };
  statement: { competencia: string; empresa: { codigo_siagri: string; razao: string; cnpj: string }; tipo_importacao: 'Extrato'; colaboradores: PreviewEmployee[] };
};
export const payrollPreview = {
  generate(company: number, file: File, competence: string, options: { signal?: AbortSignal } = {}) {
    const body = new FormData();
    body.append('file', file);
    body.append('competence', competence);
    return request<PayrollPreviewResponse>(`/companies/${company}/payroll-import-preview`, { method: 'POST', body, ...options });
  },
};
