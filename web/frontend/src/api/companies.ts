import { request } from './client';
export type Company = { id: number; codigo_siagri: string | null; razao: string | null; fantasia: string | null; cnpj: string | null; status: string | null };
export type CompanyInput = Omit<Company, 'id'>;
export const companies = {
  list: () => request<Company[]>('/companies'),
  save: (data: CompanyInput, id?: number) => request<Company>(`/companies${id ? `/${id}` : ''}`, { method: id ? 'PATCH' : 'POST', body: JSON.stringify(data) }),
  remove: (id: number) => request<void>(`/companies/${id}`, { method: 'DELETE' }),
};
