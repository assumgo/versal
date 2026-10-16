import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import App from '../App';
const company = { id: 1, codigo_siagri: '1', razao: 'Empresa Alpha', fantasia: '', cnpj: '', status: 'Ativa' };
function mockApi(expired = false) {
  const calls: string[] = [];
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const path = new URL(url, 'http://localhost').pathname;
    calls.push(`${init?.method ?? 'GET'} ${path}`);
    if (path.endsWith('/refresh')) return Response.json(expired ? {} : { access_token: 'memory-token' }, { status: expired ? 401 : 200 });
    if (path.endsWith('/login')) return Response.json({ access_token: 'login-token' });
    if (path.endsWith('/me')) return Response.json({ id: 1, email: 'test@example.com', role: 'Administrador', is_active: true });
    if (path.endsWith('/employees')) return Response.json([]);
    if (path.endsWith('/companies')) return Response.json([company, { ...company, id: 2, razao: 'Empresa Beta' }]);
    return new Response(null, { status: 204 });
  }));
  return calls;
}
afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState({}, '', '/'); });
it('redirects an anonymous protected route and logs in to the requested screen', async () => {
  window.history.replaceState({}, '', '/colaboradores');
  mockApi(true);
  render(<App />);
  await userEvent.type(await screen.findByLabelText('E-mail'), 'test@example.com');
  await userEvent.type(screen.getByLabelText('Senha'), 'password');
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));
  await waitFor(() => expect(screen.getByRole('heading', { name: 'Colaboradores' })).toBeVisible());
  expect(localStorage.length).toBe(0);
  expect(sessionStorage.length).toBe(0);
});
it('restores the session and switches the active company', async () => {
  const calls = mockApi();
  render(<App />);
  await screen.findByRole('option', { name: 'Empresa Beta' });
  await userEvent.click(screen.getByRole('button', { name: 'Colaboradores' }));
  await userEvent.selectOptions(screen.getByLabelText('Empresa ativa'), '2');
  await waitFor(() => expect(calls).toContain('GET /api/v1/companies/2/employees'));
});
