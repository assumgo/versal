import { afterEach, expect, it, vi } from 'vitest';
import { setToken } from '../api/client';
import { payrollImports } from '../api/payrollImports';

afterEach(() => { vi.unstubAllGlobals(); setToken(null); });

it('confirms by resending the file, selected competence and preview hash', async () => {
  let sent: RequestInit | undefined;
  vi.stubGlobal('fetch', vi.fn(async (_url: string, init: RequestInit) => {
    sent = init;
    return Response.json({ import_id: 9 });
  }));
  const file = new File(['same content'], 'payroll.pdf', { type: 'application/pdf' });
  await payrollImports.confirm(7, file, '09/2026', 'a'.repeat(64));
  expect(sent?.method).toBe('POST');
  expect(sent?.body).toBeInstanceOf(FormData);
  const body = sent?.body as FormData;
  expect([...body.keys()].sort()).toEqual(['competence', 'file', 'preview_sha256']);
  expect(body.get('file')).toBe(file);
  expect(body.get('competence')).toBe('09/2026');
  expect(body.get('preview_sha256')).toBe('a'.repeat(64));
  expect(new Headers(sent?.headers).has('Content-Type')).toBe(false);
});

it('requests a paged metadata-only history', async () => {
  let url = '';
  vi.stubGlobal('fetch', vi.fn(async (input: string) => {
    url = input;
    return Response.json({ items: [], offset: 50, limit: 50, total: 51 });
  }));
  const page = await payrollImports.list(7, { offset: 50, limit: 50 });
  expect(new URL(url).pathname).toBe('/api/v1/companies/7/payroll-imports');
  expect(new URL(url).searchParams.get('offset')).toBe('50');
  expect(new URL(url).searchParams.get('limit')).toBe('50');
  expect(page).toEqual({ items: [], offset: 50, limit: 50, total: 51 });
});
