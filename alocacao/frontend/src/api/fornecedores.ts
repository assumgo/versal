import { api } from './client';

export type Fornecedor = {
  id: number;
  razao_social: string;
  nome_fantasia: string;
  documento: string;
  ativo: boolean;
  created_at: string;
  updated_at: string;
};

export type FornecedorInput = {
  razao_social: string;
  nome_fantasia: string;
  documento: string;
  ativo?: boolean;
};

export const fornecedoresApi = {
  list: () => api<Fornecedor[]>('/api/fornecedores'),
  create: (payload: FornecedorInput) =>
    api<Fornecedor>('/api/fornecedores', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  update: (id: number, payload: Partial<FornecedorInput>) =>
    api<Fornecedor>(`/api/fornecedores/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  remove: (id: number) =>
    api<void>(`/api/fornecedores/${id}`, {
      method: 'DELETE',
    }),
};
