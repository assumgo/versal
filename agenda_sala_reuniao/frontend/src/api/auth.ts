import { request, setToken } from './client';

export type User = {
  id: number; name: string; email: string; is_admin: boolean; is_active: boolean; must_change_password: boolean;
};

export const me = () => request<User>('/auth/me');

export async function login(email: string, password: string) {
  const data = await request<{ access_token: string }>('/auth/login', {
    method: 'POST', body: JSON.stringify({ email, password }),
  }, false);
  setToken(data.access_token);
  return me();
}

export async function logout() {
  await request('/auth/logout', { method: 'POST' }, false);
  setToken(null);
}

export function changePassword(currentPassword: string, newPassword: string) {
  return request<User>('/auth/password', {
    method: 'POST',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}
