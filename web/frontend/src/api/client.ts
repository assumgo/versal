const base = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(/\/$/, '');
let token: string | null = null;
let refreshFlight: Promise<void> | null = null;
let generation = 0;
const listeners = new Set<() => void>();
export function onSessionExpired(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; }
export function setToken(value: string | null) { token = value; generation++; }
export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
async function decode(response: Response) {
  if (response.ok) return response.status === 204 ? undefined : response.json();
  let detail: unknown;
  try { detail = (await response.json()).detail; } catch { /* An empty error response uses the fallback. */ }
  throw new ApiError(response.status, response.status === 403 ? 'Sem permissão para acessar este recurso.' : response.status === 401 ? 'Sessão expirada. Entre novamente.' : Array.isArray(detail) ? detail.map(item => `${item.loc?.slice(1).join('.')}: ${item.msg}`).join('; ') : typeof detail === 'string' ? detail : 'Não foi possível concluir a solicitação.');
}
export async function refreshSession() {
  if (!refreshFlight) {
    const started = generation;
    refreshFlight = (async () => {
      try {
        const data = await decode(await fetch(`${base}/auth/refresh`, { method: 'POST', credentials: 'include' }));
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
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
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
  return decode(response);
}
export function errorMessage(error: unknown) { return error instanceof Error ? error.message : 'Não foi possível conectar ao servidor.'; }
