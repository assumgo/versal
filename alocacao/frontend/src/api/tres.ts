import { API_URL, api } from './client';

export type TreTipo = 'entrega' | 'devolucao';

export type TreItem = {
  id: number;
  equipamento_id: number | null;
  quantidade: number;
  categoria_nome: string;
  descricao: string;
  numero_patrimonio: string;
};

export type Tre = {
  id: number;
  codigo: string;
  tipo: TreTipo;
  colaborador_id: number;
  colaborador_nome: string;
  created_at: string;
  itens: TreItem[];
};

export type TreFilters = {
  nome?: string;
  codigo?: string;
  data_inicio?: string;
  data_fim?: string;
};

export const tresApi = {
  list: (filters: TreFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.nome?.trim()) params.set('nome', filters.nome.trim());
    if (filters.codigo?.trim()) params.set('codigo', filters.codigo.trim());
    if (filters.data_inicio) params.set('data_inicio', filters.data_inicio);
    if (filters.data_fim) params.set('data_fim', filters.data_fim);
    const query = params.toString();
    return api<Tre[]>(`/api/tres${query ? `?${query}` : ''}`);
  },
  pdfUrl: (id: number) => `${API_URL}/api/tres/${id}/pdf`,
};
