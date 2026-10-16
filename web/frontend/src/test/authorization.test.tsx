import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import App from '../App';
afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState({}, '', '/'); });
it.each(['Consulta', 'Contador', 'Operador'])('hides company mutation controls from %s', async role => {
  window.history.replaceState({}, '', '/empresas');
  vi.stubGlobal('fetch', vi.fn(async (url: string) => Response.json(url.endsWith('/refresh') ? { access_token: 'token' } : url.endsWith('/me') ? { id: 1, email: 'reader@example.com', role } : [])));
  render(<App />);
  await screen.findByRole('region', { name: 'Empresas cadastradas' });
  expect(screen.queryByRole('button', { name: 'Nova empresa' })).not.toBeInTheDocument();
});
