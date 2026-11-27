const base = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
const TOKEN_KEY = 'gestao.token';

let token: string | null = sessionStorage.getItem(TOKEN_KEY);
const listeners = new Set<() => void>();

export function getToken() {
  return token;
}

export function onSessionChange(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

export function setToken(value: string | null) {
  token = value;
  if (value) sessionStorage.setItem(TOKEN_KEY, value);
  else sessionStorage.removeItem(TOKEN_KEY);
  listeners.forEach(listener => listener());
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail: unknown) {
    super(message);
  }
}

export function openTaskCount(error: unknown): number | null {
  if (!(error instanceof ApiError) || error.status !== 409 || !error.detail || typeof error.detail !== 'object') return null;
  const detail = error.detail as { code?: string; open_task_count?: number };
  return detail.code === 'open_tasks' && typeof detail.open_task_count === 'number' ? detail.open_task_count : null;
}

async function decode(response: Response) {
  if (response.ok) return response.status === 204 ? undefined : response.json();
  let body: { detail?: unknown } | null = null;
  try { body = await response.json(); } catch { /* Resposta vazia usa a mensagem padrão. */ }
  const detail = body?.detail;
  let message = 'Não foi possível concluir a solicitação.';
  if (typeof detail === 'string') message = detail;
  else if (Array.isArray(detail)) message = detail.map(item => (typeof item?.msg === 'string' ? item.msg : 'Dado inválido')).join(' ');
  else if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') message = detail.message;
  throw new ApiError(response.status, message, detail);
}

export async function api<T>(path: string, options: RequestInit = {}, authenticated = true): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (authenticated && token) headers.set('Authorization', `Bearer ${token}`);
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(0, 'Não foi possível conectar ao servidor.', null);
  }
  if (response.status === 401 && authenticated) setToken(null);
  return decode(response);
}

export type User = { id: number; name: string; email: string };
export type Template = { key: string; name: string; phases: { name: string; tasks: string[] }[] };
export type ProjectSummary = { ativos: number; no_prazo: number; atencao: number; atrasados: number };
export type ProjectListItem = {
  id: number;
  name: string;
  status: string;
  health: string;
  owner: User;
  due_date: string | null;
  progress: number;
  next_overdue_on: string | null;
  total_tasks: number;
  done_tasks: number;
};
export type ProjectList = { today: string; summary: ProjectSummary; projects: ProjectListItem[] };
export type PhaseItem = {
  id: number;
  name: string;
  status: string;
  position: number;
  start_date: string | null;
  due_date: string | null;
  progress: number;
  total_tasks: number;
  done_tasks: number;
  overdue_tasks: number;
};
export type TaskConflict = { id: number; title: string; phase_id: number; phase_name: string; due_date: string };
export type ProjectContext = {
  project_id: number;
  project_name: string;
  project_status: string;
  project_health: string;
  project_progress: number;
  project_due_date: string | null;
  project_owner: User;
};
export type ProjectDetail = ProjectContext & {
  description: string;
  start_date: string | null;
  total_tasks: number;
  done_tasks: number;
  overdue_tasks: number;
  blocked_tasks: number;
  phases: PhaseItem[];
  schedule_conflicts: TaskConflict[];
  events: import('./format').ActivityEvent[];
};
export type TaskItem = {
  id: number;
  phase_id: number;
  phase_name: string;
  title: string;
  status: string;
  assignee: User | null;
  due_date: string | null;
  overdue: boolean;
  blocked_reason: string | null;
  position: number;
};
export type PhaseDetail = ProjectContext & {
  id: number;
  name: string;
  status: string;
  progress: number;
  start_date: string | null;
  due_date: string | null;
  total_tasks: number;
  done_tasks: number;
  overdue_tasks: number;
  tasks: TaskItem[];
};
export type TaskDetail = ProjectContext & {
  id: number;
  phase_id: number;
  phase_name: string;
  phase_progress: number;
  phase_total_tasks: number;
  phase_done_tasks: number;
  title: string;
  description: string;
  status: string;
  assignee: User | null;
  due_date: string | null;
  blocked_reason: string | null;
  overdue: boolean;
  events: import('./format').ActivityEvent[];
};
