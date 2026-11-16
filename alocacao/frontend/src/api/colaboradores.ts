import { api } from './client';

export type Colaborador = {
  id: number;
  nome: string;
  email_pessoal: string;
  cpf: string;
  data_nascimento: string;
  celular: string;
  ativo: boolean;
  created_at: string;
  updated_at: string;
};

export type ColaboradorInput = {
  nome: string;
  email_pessoal: string;
  cpf: string;
  data_nascimento: string;
  celular: string;
  ativo?: boolean;
};

export const colaboradoresApi = {
  list: () => api<Colaborador[]>('/api/colaboradores'),
  create: (payload: ColaboradorInput) =>
    api<Colaborador>('/api/colaboradores', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  update: (id: number, payload: Partial<ColaboradorInput>) =>
    api<Colaborador>(`/api/colaboradores/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  remove: (id: number) =>
    api<void>(`/api/colaboradores/${id}`, {
      method: 'DELETE',
    }),
};
