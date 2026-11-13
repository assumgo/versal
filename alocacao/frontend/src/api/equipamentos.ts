import { api } from './client';

export type EquipamentoStatus = 'disponivel' | 'alocado';

export type Equipamento = {
  id: number;
  descricao: string;
  marca: string;
  modelo: string;
  numero_serie: string;
  numero_patrimonio: string;
  mac_address: string | null;
  categoria_id: number;
  categoria_nome: string;
  status: EquipamentoStatus;
  created_at: string;
  updated_at: string;
};

export type EquipamentoInput = {
  descricao: string;
  marca: string;
  modelo: string;
  numero_serie: string;
  numero_patrimonio: string;
  mac_address?: string | null;
  categoria_id: number;
};

export type EquipamentoFilters = {
  categoria_id?: number | null;
  status?: EquipamentoStatus | '';
};

export const equipamentosApi = {
  list: (filters: EquipamentoFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.categoria_id) params.set('categoria_id', String(filters.categoria_id));
    if (filters.status) params.set('status', filters.status);
    const query = params.toString();
    return api<Equipamento[]>(`/api/equipamentos${query ? `?${query}` : ''}`);
  },
  create: (payload: EquipamentoInput) =>
    api<Equipamento>('/api/equipamentos', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  update: (id: number, payload: Partial<EquipamentoInput>) =>
    api<Equipamento>(`/api/equipamentos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  remove: (id: number) =>
    api<void>(`/api/equipamentos/${id}`, {
      method: 'DELETE',
    }),
};
