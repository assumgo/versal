import { request } from './client';
export type Employee = { id: number; company_id: number | null; nome: string | null; cpf: string | null; matricula: string | null; cargo: string | null; centro_custo: string | null; codigo_correntista: string | null; status: string | null };
export type EmployeeInput = Omit<Employee, 'id' | 'company_id'>;
export const employees = {
  list: (company: number) => request<Employee[]>(`/companies/${company}/employees`),
  save: (company: number, data: EmployeeInput, id?: number) => request<Employee>(`/companies/${company}/employees${id ? `/${id}` : ''}`, { method: id ? 'PATCH' : 'POST', body: JSON.stringify(data) }),
  remove: (company: number, id: number) => request<void>(`/companies/${company}/employees/${id}`, { method: 'DELETE' }),
};
