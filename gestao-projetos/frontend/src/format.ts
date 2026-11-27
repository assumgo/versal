import { statusLabel } from './labels';

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return 'Sem prazo';
  const [year, month, day] = iso.slice(0, 10).split('-');
  if (!year || !month || !day) return iso;
  return `${day}/${month}/${year}`;
}

export function formatWhen(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(iso));
}

const EVENT_LABEL: Record<string, string> = {
  project_created: 'Criou o projeto',
  project_status_changed: 'Alterou o status',
  project_owner_changed: 'Alterou o responsável',
  project_due_date_changed: 'Alterou o prazo',
  task_created: 'Criou a tarefa',
  task_status_changed: 'Alterou o status',
  task_assignee_changed: 'Alterou o responsável',
  task_due_date_changed: 'Alterou o prazo',
};

const VALUE_KIND: Record<string, 'status' | 'date' | 'text'> = {
  project_status_changed: 'status',
  task_status_changed: 'status',
  project_due_date_changed: 'date',
  task_due_date_changed: 'date',
};

export type ActivityEvent = {
  id: number;
  event_type: string;
  old_value: string | null;
  new_value: string | null;
  actor_name: string;
  created_at: string;
};

function eventValue(kind: 'status' | 'date' | 'text', value: string | null): string {
  if (!value) return 'nenhum';
  if (kind === 'status') return statusLabel(value);
  if (kind === 'date') return formatDate(value);
  return value;
}

export function eventText(event: ActivityEvent): string {
  const label = EVENT_LABEL[event.event_type] ?? 'Registrou uma mudança';
  if (event.event_type.endsWith('_created')) return `${label} “${event.new_value ?? ''}”`;
  const kind = VALUE_KIND[event.event_type] ?? 'text';
  if (!event.old_value) return `${label} para ${eventValue(kind, event.new_value)}`;
  return `${label} de ${eventValue(kind, event.old_value)} para ${eventValue(kind, event.new_value)}`;
}
