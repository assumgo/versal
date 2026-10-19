import { request } from './client';

export type PayrollImportCreated = {
  import_id: number; company_id: number; competence: string; filename: string; size_bytes: number;
  sha256: string; imported_at: string; employees: number; rubrics: number;
  totals_by_type: Record<string, string>; net_total: string;
};
export type PayrollImportHistoryItem = {
  import_id: number; company_id: number; competence: string | null; filename: string | null;
  status: string | null; imported_at: string | null; size_bytes: number | null; sha256: string | null;
  employees: number | null; rubrics: number | null;
};
export type PayrollImportHistoryPage = {
  items: PayrollImportHistoryItem[]; offset: number; limit: number; total: number;
};

export const payrollImports = {
  confirm(company: number, file: File, competence: string, previewSha256: string,
          options: { signal?: AbortSignal } = {}) {
    const body = new FormData();
    body.append('file', file);
    body.append('competence', competence);
    body.append('preview_sha256', previewSha256);
    return request<PayrollImportCreated>(`/companies/${company}/payroll-imports`, {
      method: 'POST', body, ...options,
    });
  },
  list(company: number, query: { offset?: number; limit?: number } = {},
       options: { signal?: AbortSignal } = {}) {
    const params = new URLSearchParams();
    params.set('offset', String(query.offset ?? 0));
    params.set('limit', String(query.limit ?? 50));
    return request<PayrollImportHistoryPage>(
      `/companies/${company}/payroll-imports?${params.toString()}`, options,
    );
  },
};
