import { request } from './client';
export type Account = { id: number; email: string; name: string | null; login: string | null; role: string; is_active: boolean };
export type AccountUpdate = { name?: string | null; login?: string; role?: string; is_active?: boolean };
export const users = {
  list: () => request<Account[]>('/users'),
  update: (id: number, data: AccountUpdate) => request<Account>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  inactivate: (id: number) => request<void>(`/users/${id}`, { method: 'DELETE' }),
  remove: (id: number) => request<void>(`/users/${id}/permanent`, { method: 'DELETE' }),
};
