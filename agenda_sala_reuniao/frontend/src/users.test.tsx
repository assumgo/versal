import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import App from './App';

const admin = { id: 1, name: 'TI Versal', email: 'ti@versalagro.com.br', is_admin: true, is_active: true, must_change_password: false };
const created = { id: 3, name: 'Marize Matos', email: 'marize.matos@versalagro.com.br', is_admin: false, is_active: true, must_change_password: true };

afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState({}, '', '/'); });

it('creates an account without losing the form and asks for a password change on first access', async () => {
  let users = [admin];
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const path = new URL(url, 'http://localhost').pathname;
    const method = init?.method ?? 'GET';
    if (path.endsWith('/auth/refresh')) return Response.json({ access_token: 'memory-token' });
    if (path.endsWith('/auth/me')) return Response.json(admin);
    if (path.endsWith('/users') && method === 'POST') {
      users = [...users, created];
      return Response.json(created, { status: 201 });
    }
    if (path.endsWith('/users')) return Response.json(users);
    if (path.endsWith('/require-password-change')) {
      return Response.json({ ...admin, must_change_password: true });
    }
    return Response.json([]);
  }));
  window.history.replaceState({}, '', '/usuarios');
  render(<App />);
  expect(await screen.findByRole('heading', { name: 'Usuários' })).toBeVisible();
  await userEvent.type(screen.getByLabelText('Nome'), 'Marize Matos');
  await userEvent.type(screen.getByLabelText('E-mail'), 'marize.matos@versalagro.com.br');
  await userEvent.type(screen.getByLabelText('Senha'), 'senha-inicial');
  await userEvent.click(screen.getByRole('button', { name: 'Criar conta' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Conta criada. A pessoa troca a senha no primeiro acesso.');
  expect(screen.getByText('marize.matos@versalagro.com.br')).toBeVisible();
  expect(screen.getByLabelText('Nome')).toHaveValue('');
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  await userEvent.click(screen.getAllByRole('button', { name: 'Exigir troca de senha' })[0]);
  expect(await screen.findByText('TI Versal vai trocar a senha no próximo acesso.')).toBeVisible();
});

it('blocks the agenda until the new password is saved', async () => {
  const pending = { ...created, id: 8, name: 'Marina' };
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const path = new URL(url, 'http://localhost').pathname;
    if (path.endsWith('/auth/refresh')) return Response.json({ access_token: 'memory-token' });
    if (path.endsWith('/auth/password')) return Response.json({ ...pending, must_change_password: false });
    if (path.endsWith('/auth/me')) return Response.json(pending);
    if (path.includes('/reservations')) return Response.json([]);
    return new Response(null, { status: init?.method === 'POST' ? 204 : 200 });
  }));
  render(<App />);
  expect(await screen.findByRole('heading', { name: 'Defina uma nova senha' })).toBeVisible();
  expect(screen.queryByRole('heading', { name: 'Painel' })).not.toBeInTheDocument();
  await userEvent.type(screen.getByLabelText('Senha atual'), 'senha-inicial');
  await userEvent.type(screen.getByLabelText('Nova senha'), 'senha-nova-456');
  await userEvent.type(screen.getByLabelText('Confirmar nova senha'), 'senha-nova-456');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar senha' }));
  expect(await screen.findByRole('heading', { name: 'Painel' })).toBeVisible();
});
