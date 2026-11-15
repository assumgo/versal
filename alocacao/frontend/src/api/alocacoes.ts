import { api } from './client';

export type AlocacaoTipo = 'entrega' | 'devolucao';
export type DestinoTipo = 'colaborador' | 'local' | 'manutencao';

export type Alocacao = {
  id: number;
  codigo: string;
  tipo: AlocacaoTipo;
  destino_tipo: DestinoTipo;
  equipamento_id: number;
  equipamento_codigo: string;
  produto_id: number;
  produto_codigo: string;
  produto_descricao: string;
  numero_patrimonio: string;
  quantidade: number;
  colaborador_id: number | null;
  colaborador_nome: string;
  local_id: number | null;
  local_nome: string;
  destino_nome: string;
  tre_id: number | null;
  tre_codigo: string;
  referencia_id: number | null;
  data_previsao: string | null;
  ativa: boolean;
  estoque_disponivel_produto: number;
  created_at: string;
  updated_at: string;
};

export type AlocacaoInput = {
  tipo: AlocacaoTipo;
  destino_tipo: DestinoTipo;
  equipamento_id: number;
  quantidade: number;
  colaborador_id?: number | null;
  local_id?: number | null;
  data_previsao?: string | null;
};

export type AlocacaoFilters = {
  ativa?: boolean | null;
  tipo?: AlocacaoTipo | '';
  q?: string;
};

export const alocacoesApi = {
  list: (filters: AlocacaoFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.ativa === true || filters.ativa === false) params.set('ativa', String(filters.ativa));
    if (filters.tipo) params.set('tipo', filters.tipo);
    if (filters.q?.trim()) params.set('q', filters.q.trim());
    const query = params.toString();
    return api<Alocacao[]>(`/api/alocacoes${query ? `?${query}` : ''}`);
  },
  create: (payload: AlocacaoInput) =>
    api<Alocacao>('/api/alocacoes', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  remove: (id: number) =>
    api<void>(`/api/alocacoes/${id}`, {
      method: 'DELETE',
    }),
};
