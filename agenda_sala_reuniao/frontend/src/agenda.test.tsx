import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import App from './App';

const room = { id: 1, name: 'Sala Verde', location: '1º andar', capacity: 8, is_active: true };

afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState({}, '', '/'); });

it('shows the conflict on the reservation form and keeps the day empty', async () => {
  const calls: { method: string; path: string; body?: string }[] = [];
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const path = new URL(url, 'http://localhost').pathname;
    const method = init?.method ?? 'GET';
    calls.push({ method, path, body: typeof init?.body === 'string' ? init.body : undefined });
    if (path.endsWith('/auth/refresh')) return Response.json({ access_token: 'memory-token' });
    if (path.endsWith('/auth/me')) return Response.json({ id: 2, name: 'Ana', email: 'ana@agenda.test', is_admin: false, is_active: true });
    if (path.endsWith('/rooms')) return Response.json([room]);
    if (path.endsWith('/reservations') && method === 'POST') {
      return Response.json({ detail: 'Esta sala já está reservada nesse horário.' }, { status: 409 });
    }
    if (path.includes('/reservations')) return Response.json([]);
    return new Response(null, { status: 204 });
  }));
  render(<App />);
  expect(await screen.findByRole('heading', { name: 'Painel' })).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Agenda' }));
  expect(await screen.findByRole('heading', { name: 'Agenda' })).toBeVisible();
  await screen.findAllByRole('option', { name: 'Sala Verde' });
  await userEvent.selectOptions(screen.getByLabelText('Sala'), '1');
  await userEvent.type(screen.getByLabelText('Título'), 'Planejamento');
  fireEvent.change(screen.getByLabelText('Data de início'), { target: { value: '2026-11-04' } });
  fireEvent.change(screen.getByLabelText('Hora de início'), { target: { value: '09:00' } });
  fireEvent.change(screen.getByLabelText('Data de fim'), { target: { value: '2026-11-04' } });
  fireEvent.change(screen.getByLabelText('Hora de fim'), { target: { value: '10:00' } });
  await userEvent.click(screen.getByRole('button', { name: 'Reservar' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Esta sala já está reservada nesse horário.');
  expect(screen.getByText('Nenhuma reserva neste dia.')).toBeVisible();
  const posted = calls.find(call => call.method === 'POST' && call.path.endsWith('/reservations'));
  expect(JSON.parse(posted?.body ?? '{}')).toMatchObject({
    room_id: 1, title: 'Planejamento',
    starts_at: '2026-11-04T12:00:00.000Z', ends_at: '2026-11-04T13:00:00.000Z',
  });
});
