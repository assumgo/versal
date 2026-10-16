import { afterEach, expect, it, vi } from 'vitest';
import { request, setToken, refreshSession } from '../api/client';
afterEach(() => { setToken(null); vi.unstubAllGlobals(); });
it('shares a refresh across concurrent unauthorized requests and retries once with credentials', async () => {
  setToken('old'); let refreshes = 0; const credentials: unknown[] = [];
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit) => {
    credentials.push(init.credentials);
    if (url.endsWith('/refresh')) { refreshes++; return Response.json({ access_token: 'new' }); }
    return (init.headers as Record<string, string>).Authorization === 'Bearer new' ? Response.json({ ok: true }) : new Response(null, { status: 401 });
  }));
  expect(await Promise.all([request('/companies'), request('/companies')])).toEqual([{ ok: true }, { ok: true }]);
  expect(refreshes).toBe(1);
  expect(credentials.every(value => value === 'include')).toBe(true);
});
it('does not refresh a forbidden response', async () => {
  const fetcher = vi.fn().mockResolvedValue(Response.json({ detail: 'Forbidden' }, { status: 403 })); vi.stubGlobal('fetch', fetcher);
  await expect(request('/companies')).rejects.toMatchObject({ status: 403 });
  expect(fetcher).toHaveBeenCalledTimes(1);
});
it('stops after a second unauthorized response', async () => {
  const fetcher = vi.fn(async (url: string) => url.endsWith('/refresh') ? Response.json({ access_token: 'new' }) : new Response(null, { status: 401 })); vi.stubGlobal('fetch', fetcher);
  await expect(request('/companies')).rejects.toMatchObject({ status: 401 });
  expect(fetcher).toHaveBeenCalledTimes(3);
});
it('does not restore a token when an earlier refresh completes after session clearing', async () => {
  let finish!: (value: Response) => void;
  vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(resolve => { finish = resolve; })));
  const refresh = refreshSession(); setToken(null); finish(Response.json({ access_token: 'stale' })); await refresh;
  const fetcher = vi.fn().mockResolvedValue(Response.json([])); vi.stubGlobal('fetch', fetcher); await request('/companies');
  expect(fetcher.mock.calls[0][1].headers.Authorization).toBeUndefined();
});
it('never replays an old mutation under a newly logged-in session', async () => {
  setToken('old-user'); let finish!: (value: Response) => void;
  const fetcher = vi.fn(() => new Promise<Response>(resolve => { finish = resolve; })); vi.stubGlobal('fetch', fetcher);
  const operation = request('/companies/1', { method: 'DELETE' });
  setToken('new-user'); finish(new Response(null, { status: 401 }));
  // A second send would hang on this deferred mock; provide a response to expose replay.
  fetcher.mockResolvedValue(Response.json({}));
  await expect(operation).rejects.toMatchObject({ status: 401 });
  expect(fetcher).toHaveBeenCalledTimes(1);
});
it('does not clear the new session when an old retry returns unauthorized', async () => {
  setToken('old'); let finish!: (value: Response) => void;
  let count = 0;
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.endsWith('/refresh')) return Response.json({ access_token: 'refreshed' });
    count++;
    if (count === 1) return new Response(null, { status: 401 });
    return new Promise<Response>(resolve => { finish = resolve; });
  }));
  const operation = request('/companies');
  // Wait for the retry rather than timing the network.
  while (!finish) await Promise.resolve();
  setToken('new-user'); finish(new Response(null, { status: 401 }));
  await expect(operation).rejects.toMatchObject({ status: 401 });
  const fetcher = vi.fn().mockResolvedValue(Response.json([])); vi.stubGlobal('fetch', fetcher); await request('/companies');
  expect(fetcher.mock.calls[0][1].headers.Authorization).toBe('Bearer new-user');
});
