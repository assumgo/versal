import { api } from './client';

export type Categoria = {
  id: number;
  nome: string;
  descricao: string | null;
  ativo: boolean;
  created_at: string;
  updated_at: string;
};

export type CategoriaInput = {
  nome: string;
  descricao?: string | null;
  ativo?: boolean;
};

export const categoriasApi = {
  list: (ativo?: boolean) => {
    const query = typeof ativo === 'boolean' ? `?ativo=${ativo}` : '';
    return api<Categoria[]>(`/api/categorias${query}`);
  },
  create: (payload: CategoriaInput) =>
    api<Categoria>('/api/categorias', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  update: (id: number, payload: Partial<CategoriaInput>) =>
    api<Categoria>(`/api/categorias/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  remove: (id: number) =>
    api<void>(`/api/categorias/${id}`, {
      method: 'DELETE',
    }),
};
