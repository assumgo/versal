import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import { users } from '../api/users';
import { Users } from '../pages/Users';

vi.mock('../api/users', () => ({ users: { list: vi.fn(), update: vi.fn(), inactivate: vi.fn(), remove: vi.fn() } }));
afterEach(() => vi.resetAllMocks());

const account = { id: 4, email: 'maria@example.test', name: 'Maria', login: 'maria', role: 'Consulta', is_active: true };

it('hides administration and does not load users without permission', () => {
  render(<Users canWrite={false} />);
  expect(screen.getByRole('alert')).toHaveTextContent('Sem permissão');
  expect(screen.queryByRole('button', { name: 'Editar' })).not.toBeInTheDocument();
  expect(users.list).not.toHaveBeenCalled();
});

it('edits name, login and keeps the administrator switch aligned with the role', async () => {
  vi.mocked(users.list).mockResolvedValue([account]);
  vi.mocked(users.update).mockResolvedValue({ ...account, name: 'Maria Souza', login: 'msouza', role: 'Administrador' });
  render(<Users canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Editar' }));
  expect(screen.getByLabelText('E-mail')).toHaveValue('maria@example.test');
  expect(screen.getByRole('checkbox', { name: 'Administrador' })).not.toBeChecked();
  await userEvent.clear(screen.getByLabelText('Nome'));
  await userEvent.type(screen.getByLabelText('Nome'), 'Maria Souza');
  await userEvent.clear(screen.getByLabelText('Login'));
  await userEvent.type(screen.getByLabelText('Login'), 'msouza');
  await userEvent.click(screen.getByRole('checkbox', { name: 'Administrador' }));
  expect(screen.getByLabelText('Papel')).toHaveValue('Administrador');
  await userEvent.click(screen.getByRole('checkbox', { name: 'Administrador' }));
  expect(screen.getByLabelText('Papel')).toHaveValue('Operador');
  await userEvent.selectOptions(screen.getByLabelText('Papel'), 'Contador');
  expect(screen.getByRole('checkbox', { name: 'Administrador' })).not.toBeChecked();
  await userEvent.selectOptions(screen.getByLabelText('Papel'), 'Administrador');
  expect(screen.getByRole('checkbox', { name: 'Administrador' })).toBeChecked();
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));
  expect(await screen.findByText('Registro salvo.')).toBeVisible();
  expect(users.update).toHaveBeenCalledWith(4, { name: 'Maria Souza', login: 'msouza', role: 'Administrador' });
});

it('confirms inactivation and permanent deletion', async () => {
  vi.mocked(users.list).mockResolvedValue([account]);
  vi.mocked(users.inactivate).mockResolvedValue(undefined);
  vi.mocked(users.remove).mockResolvedValue(undefined);
  render(<Users canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Inativar' }));
  expect(users.inactivate).not.toHaveBeenCalled();
  expect(screen.getByText('O usuário deixa de acessar o sistema. O cadastro e o histórico permanecem.')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }));
  expect(await screen.findByText('Usuário inativado.')).toBeVisible();
  expect(users.inactivate).toHaveBeenCalledWith(4);
  await userEvent.click(await screen.findByRole('button', { name: 'Excluir' }));
  expect(screen.getByText('A exclusão é definitiva. O histórico permanece, sem o vínculo com este usuário.')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }));
  expect(await screen.findByText('Usuário excluído.')).toBeVisible();
  expect(users.remove).toHaveBeenCalledWith(4);
});

it('reactivates an inactive user and shows the last-administrator error', async () => {
  vi.mocked(users.list).mockResolvedValue([{ ...account, is_active: false }]);
  vi.mocked(users.update).mockRejectedValueOnce(new ApiError(409, 'É necessário manter um administrador ativo')).mockResolvedValue(account);
  render(<Users canWrite />);
  await userEvent.click(await screen.findByRole('button', { name: 'Reativar' }));
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('É necessário manter um administrador ativo');
  expect(users.update).toHaveBeenCalledWith(4, { is_active: true });
  expect(screen.queryByRole('button', { name: 'Inativar' })).not.toBeInTheDocument();
});
