const base = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8010/api/v1').replace(/\/$/, '');
let token: string | null = null;
let refreshFlight: Promise<void> | null = null;
let generation = 0;
const listeners = new Set<() => void>();

export function onSessionExpired(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

export function setToken(value: string | null) {
  token = value;
  generation += 1;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

function messageFor(status: number, detail: unknown, path: string) {
  if (status === 403) return 'Sem permissão para acessar este recurso.';
  if (status === 401) return path.endsWith('/auth/login') ? 'E-mail ou senha inválidos.' : 'Sessão expirada. Entre novamente.';
  if (Array.isArray(detail)) return detail.map(item => item.msg).join('; ');
  if (typeof detail === 'string') return detail;
  return 'Não foi possível concluir a solicitação.';
}

async function decode(response: Response, path: string) {
  if (response.ok) return response.status === 204 ? undefined : response.json();
  let detail: unknown;
  try { detail = (await response.json()).detail; } catch { /* An empty error response uses the fallback. */ }
  throw new ApiError(response.status, messageFor(response.status, detail, path));
}

export async function refreshSession() {
  if (!refreshFlight) {
    const started = generation;
    refreshFlight = (async () => {
      try {
        const data = await decode(await fetch(`${base}/auth/refresh`, { method: 'POST', credentials: 'include' }), '/auth/refresh');
        if (started === generation) token = data.access_token;
      } catch (error) {
        if (started === generation) { token = null; listeners.forEach(listener => listener()); }
        throw error;
      } finally { refreshFlight = null; }
    })();
  }
  return refreshFlight;
}

export async function request<T>(path: string, options: RequestInit = {}, authenticated = true): Promise<T> {
  const send = () => {
    const headers = new Headers(options.headers);
    if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
    if (authenticated && token) headers.set('Authorization', `Bearer ${token}`);
    return fetch(`${base}${path}`, { ...options, credentials: 'include', headers });
  };
  const session = generation;
  const ensureSession = () => { if (authenticated && session !== generation) throw new ApiError(401, 'A sessão foi alterada.'); };
  const sentToken = token;
  let response = await send();
  ensureSession();
  if (response.status === 401 && authenticated) {
    if (sentToken === token) await refreshSession();
    ensureSession();
    response = await send();
    ensureSession();
    if (response.status === 401) { setToken(null); listeners.forEach(listener => listener()); }
  }
  return decode(response, path);
}

export function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Não foi possível conectar ao servidor.';
}
