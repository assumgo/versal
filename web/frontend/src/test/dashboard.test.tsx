import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import { appointments } from '../api/appointments';
import type { Company } from '../api/companies';
import { Dashboard } from '../pages/Dashboard';

vi.mock('../api/appointments', () => ({ appointments: { list: vi.fn(), create: vi.fn() } }));
afterEach(() => vi.resetAllMocks());

const company = { id: 3, codigo_siagri: '1', razao: 'Empresa Alpha', fantasia: '', cnpj: '', status: 'Ativa' } as Company;
const item = { id: 8, company_id: 3, scheduled_date: '2026-10-15', starts_at: '09:30', title: 'Fechamento da folha', details: 'Levar os recibos.' };

it('shows every day of the month, the basic appointment, and its details', async () => {
  vi.mocked(appointments.list).mockResolvedValue([item]);
  render(<Dashboard company={company} competence="2026-10" canWrite />);
  expect(await screen.findByText('09:30 Fechamento da folha')).toBeVisible();
  expect(screen.getAllByRole('button', { name: /de outubro de 2026/ })).toHaveLength(31);
  await userEvent.click(screen.getByRole('button', { name: /15 de outubro de 2026, 1 agendamento/ }));
  expect(screen.getByRole('region', { name: 'Agendamentos do dia' })).toHaveTextContent('Levar os recibos.');
  expect(screen.getByRole('heading', { name: '15 de outubro de 2026' })).toBeVisible();
});

it('schedules on the selected day and hides the form without permission', async () => {
  vi.mocked(appointments.list).mockResolvedValue([]);
  vi.mocked(appointments.create).mockResolvedValue(item);
  const { rerender } = render(<Dashboard company={company} competence="2026-10" canWrite={false} />);
  await userEvent.click(await screen.findByRole('button', { name: /15 de outubro de 2026, sem agendamentos/ }));
  expect(screen.queryByRole('button', { name: 'Agendar' })).not.toBeInTheDocument();
  rerender(<Dashboard company={company} competence="2026-10" canWrite />);
  await userEvent.click(screen.getByRole('button', { name: /15 de outubro de 2026, sem agendamentos/ }));
  await userEvent.type(screen.getByLabelText('Título'), 'Fechamento da folha');
  await userEvent.type(screen.getByLabelText('Hora'), '09:30');
  await userEvent.type(screen.getByLabelText('Detalhes'), 'Levar os recibos.');
  await userEvent.click(screen.getByRole('button', { name: 'Agendar' }));
  expect(await screen.findByText('Agendamento salvo.')).toBeVisible();
  expect(appointments.create).toHaveBeenCalledWith(3, { scheduled_date: '2026-10-15', starts_at: '09:30', title: 'Fechamento da folha', details: 'Levar os recibos.' });
});
