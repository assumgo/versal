import { api } from './client';

export type Local = {
  id: number;
  codigo: string;
  nome: string;
  descricao: string;
  created_at: string;
  updated_at: string;
};

export type LocalInput = {
  nome: string;
  descricao: string;
};

export const locaisApi = {
  list: (q?: string) => {
    const params = new URLSearchParams();
    if (q?.trim()) params.set('q', q.trim());
    const query = params.toString();
    return api<Local[]>(`/api/locais${query ? `?${query}` : ''}`);
  },
  create: (payload: LocalInput) =>
    api<Local>('/api/locais', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  update: (id: number, payload: Partial<LocalInput>) =>
    api<Local>(`/api/locais/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  remove: (id: number) =>
    api<void>(`/api/locais/${id}`, {
      method: 'DELETE',
    }),
};
