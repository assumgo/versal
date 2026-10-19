import { afterEach, expect, it, vi } from 'vitest';
import { request, setToken } from '../api/client';
import { payrollPreview } from '../api/payrollPreview';
import { previewResult } from './payrollPreviewFixtures';

afterEach(() => { vi.unstubAllGlobals(); setToken(null); });
it('sends FormData with current bearer and retries it after refresh without a JSON content type', async () => {
  setToken('old');
  const calls: RequestInit[] = [];
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit) => {
    if (url.endsWith('/auth/refresh')) return Response.json({ access_token: 'new' });
    calls.push(init);
    return calls.length === 1 ? new Response(null, { status: 401 }) : Response.json(previewResult);
  }));
  const file = new File(['synthetic'], 'input.pdf', { type: 'application/pdf' });
  const controller = new AbortController();
  await payrollPreview.generate(1, file, '09/2026', { signal: controller.signal });
  expect(calls).toHaveLength(2);
  calls.forEach((call, index) => {
    expect(call.body).toBeInstanceOf(FormData);
    const data = call.body as FormData;
    expect([...data.keys()].sort()).toEqual(['competence', 'file']);
    expect(data.get('file')).toBe(file);
    expect(data.get('competence')).toBe('09/2026');
    const headers = new Headers(call.headers);
    expect(headers.has('Content-Type')).toBe(false);
    expect(headers.get('Authorization')).toBe(`Bearer ${index ? 'new' : 'old'}`);
    expect(call.credentials).toBe('include');
    expect(call.signal).toBe(controller.signal);
  });
});
it('preserves JSON defaults and explicit Headers options', async () => {
  const fetcher = vi.fn(async (_url: string, _init: RequestInit) => Response.json({}));
  vi.stubGlobal('fetch', fetcher);
  await request('/test', { method: 'POST', body: '{}', headers: new Headers({ 'X-Test': 'value' }) });
  const headers = new Headers(fetcher.mock.calls[0][1].headers);
  expect(headers.get('Content-Type')).toBe('application/json');
  expect(headers.get('X-Test')).toBe('value');
});
