import { api } from './client';

export type Produto = {
  id: number;
  codigo: string;
  descricao: string;
  marca: string;
  modelo: string;
  categoria_id: number;
  categoria_nome: string;
  created_at: string;
  updated_at: string;
};

export type ProdutoInput = {
  codigo: string;
  descricao: string;
  marca: string;
  modelo: string;
  categoria_id: number;
};

export const produtosApi = {
  list: () => api<Produto[]>('/api/produtos'),
  create: (payload: ProdutoInput) =>
    api<Produto>('/api/produtos', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  update: (id: number, payload: Partial<ProdutoInput>) =>
    api<Produto>(`/api/produtos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  remove: (id: number) =>
    api<void>(`/api/produtos/${id}`, {
      method: 'DELETE',
    }),
};
