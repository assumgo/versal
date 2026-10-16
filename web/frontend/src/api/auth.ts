import { request, setToken } from './client';
export type User = { id: number; email: string; role: string; is_active: boolean };
export const me = () => request<User>('/auth/me');
export async function login(email: string, password: string) {
  const data = await request<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }, false);
  setToken(data.access_token);
  return me();
}
export async function logout() {
  await request('/auth/logout', { method: 'POST' }, false);
  setToken(null);
}
