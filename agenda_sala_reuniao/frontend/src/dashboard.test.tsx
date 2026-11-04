import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import App from './App';
import { saoPauloToIso, todayInSaoPaulo } from './time';

afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState({}, '', '/'); });

it('opens the dashboard after login with day, week and month totals in 24-hour time', async () => {
  const today = todayInSaoPaulo();
  const reservation = {
    id: 7, room_id: 1, room_name: 'Sala Verde', user_id: 2, user_name: 'Ana', title: 'Planejamento',
    starts_at: saoPauloToIso(`${today}T09:00`), ends_at: saoPauloToIso(`${today}T10:00`), mine: true,
  };
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const path = new URL(url, 'http://localhost').pathname;
    if (path.endsWith('/auth/refresh')) return Response.json({ access_token: 'memory-token' });
    if (path.endsWith('/auth/me')) return Response.json({ id: 2, name: 'Ana', email: 'ana@agenda.test', is_admin: false, is_active: true });
    if (path.includes('/reservations')) return Response.json([reservation]);
    return new Response(null, { status: init?.method === 'POST' ? 204 : 200 });
  }));
  render(<App />);
  expect(await screen.findByRole('heading', { name: 'Painel' })).toBeVisible();
  expect(screen.getByRole('button', { name: 'Painel' })).toHaveAttribute('aria-current', 'page');
  expect(await screen.findAllByText('Planejamento')).toHaveLength(3);
  expect(screen.getAllByRole('article').map(card => card.querySelector('strong')?.textContent)).toEqual(['1', '1', '1']);
  expect(screen.getAllByText(/09:00/).length).toBeGreaterThan(0);
  expect(screen.queryByText(/\bAM\b|\bPM\b/)).not.toBeInTheDocument();
});
