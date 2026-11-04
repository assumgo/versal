import { request } from './client';
import type { User } from './auth';

export const listUsers = () => request<User[]>('/users');
export const createUser = (body: { name: string; email: string; password: string; is_admin: boolean }) => (
  request<User>('/users', { method: 'POST', body: JSON.stringify(body) })
);
