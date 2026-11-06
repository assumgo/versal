import { request } from './client';
export type Account = { id: number; email: string; name: string | null; login: string | null; role: string; is_active: boolean };
export type AccountUpdate = { name?: string | null; login?: string; role?: string; is_active?: boolean };
export type AccountCreate = { email: string; password: string; role: string; name?: string | null; login?: string };
export const users = {
  list: () => request<Account[]>('/users'),
  create: (data: AccountCreate) => request<Account>('/users', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: AccountUpdate) => request<Account>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  inactivate: (id: number) => request<void>(`/users/${id}`, { method: 'DELETE' }),
  remove: (id: number) => request<void>(`/users/${id}/permanent`, { method: 'DELETE' }),
};
