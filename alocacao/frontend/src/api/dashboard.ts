import { api } from './client';

export type DashboardCategoria = {
  id: number;
  nome: string;
  disponiveis: number;
  alocados: number;
  em_manutencao: number;
  total: number;
};

export type DashboardSummary = {
  disponiveis: number;
  alocados: number;
  em_manutencao: number;
  total_recursos: number;
  categorias: DashboardCategoria[];
};

export const dashboardApi = {
  summary: () => api<DashboardSummary>('/api/dashboard/summary'),
};
