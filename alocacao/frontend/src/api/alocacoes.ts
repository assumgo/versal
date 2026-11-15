import { api } from './client';

export type Alocacao = {
  id: number;
  equipamento_id: number;
  equipamento_codigo: string;
  produto_codigo: string;
  produto_descricao: string;
  numero_patrimonio: string;
  colaborador_id: number | null;
  colaborador_nome: string;
  ativa: boolean;
  tre_entrega_id: number | null;
  tre_devolucao_id: number | null;
  created_at: string;
  updated_at: string;
};

export type AlocacaoResult = {
  alocacoes: Alocacao[];
  tre_id: number;
  tre_codigo: string;
  tre_tipo: string;
};

export const alocacoesApi = {
  list: (ativa: boolean | null = true) => {
    if (ativa === null) return api<Alocacao[]>('/api/alocacoes');
    return api<Alocacao[]>(`/api/alocacoes?ativa=${ativa}`);
  },
  create: (payload: { colaborador_id: number; equipamento_ids: number[] }) =>
    api<AlocacaoResult>('/api/alocacoes', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  devolver: (alocacao_ids: number[]) =>
    api<AlocacaoResult>('/api/alocacoes/devolver', {
      method: 'POST',
      body: JSON.stringify({ alocacao_ids }),
    }),
};
