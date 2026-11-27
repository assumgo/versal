export const STATUS_LABEL: Record<string, string> = {
  rascunho: 'Rascunho',
  em_andamento: 'Em andamento',
  pausado: 'Pausado',
  concluido: 'Concluído',
  cancelado: 'Cancelado',
  nao_iniciada: 'Não iniciada',
  a_fazer: 'A fazer',
  bloqueada: 'Bloqueada',
  concluida: 'Concluída',
  no_prazo: 'No prazo',
  atencao: 'Em atenção',
  atrasado: 'Atrasado',
};

export function statusLabel(value: string): string {
  return STATUS_LABEL[value] ?? value;
}

export function badgeFor(status: string, health: string): { label: string; tone: string } {
  if (status === 'rascunho') return { label: `Rascunho · ${statusLabel(health)}`, tone: health };
  if (status === 'em_andamento') return { label: statusLabel(health), tone: health };
  return { label: statusLabel(status), tone: status };
}
