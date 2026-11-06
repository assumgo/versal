import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import { reservations } from '../api/reservations';
import { RoomReservations } from '../pages/RoomReservations';

vi.mock('../api/reservations', () => ({ reservations: { list: vi.fn(), create: vi.fn() } }));
afterEach(() => vi.resetAllMocks());

const now = () => new Date(2026, 9, 15, 8, 0);
const item = { id: 8, scheduled_date: '2026-10-15', starts_at: '09:30', ends_at: '10:30', title: 'Reunião da sala', details: 'Levar o projetor.', action: 'Agendada' as const };

it('shows the month, the reservation and finishes it after the end', async () => {
  vi.mocked(reservations.list).mockResolvedValue([item]);
  render(<RoomReservations canWrite now={now} />);
  expect(await screen.findByText((_, element) => element?.classList.contains('calendar-chip') === true && element.textContent === '09:30–10:30 Reunião da sala')).toBeVisible();
  expect(screen.getByRole('heading', { name: 'Reserva de Sala - Versal' })).toBeVisible();
  expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /15 de outubro de 2026, 1 reserva/ }));
  expect(screen.getByRole('region', { name: 'Reservas do dia' })).toHaveTextContent('Ação: Agendada');
  expect(screen.getByText('Levar o projetor.')).toBeVisible();
});

it('opens the saved confirmation and can show the next month', async () => {
  vi.mocked(reservations.list).mockResolvedValue([]);
  vi.mocked(reservations.create).mockResolvedValue(item);
  render(<RoomReservations canWrite now={now} />);
  await userEvent.click(await screen.findByRole('button', { name: /15 de outubro de 2026, sem reservas/ }));
  await userEvent.type(screen.getByLabelText('Título'), 'Reunião da sala');
  await userEvent.type(screen.getByLabelText('Início'), '09:30');
  await userEvent.type(screen.getByLabelText('Fim'), '11:31');
  await userEvent.click(screen.getByRole('button', { name: 'Reservar' }));
  expect(screen.getByText('O intervalo da reserva não pode passar de 2 horas.')).toBeVisible();
  expect(reservations.create).not.toHaveBeenCalled();
  await userEvent.clear(screen.getByLabelText('Fim'));
  await userEvent.type(screen.getByLabelText('Fim'), '10:30');
  await userEvent.click(screen.getByRole('button', { name: 'Reservar' }));
  expect(await screen.findByRole('dialog', { name: 'Reserva gravada' })).toHaveTextContent('A reserva foi gravada com sucesso.');
  expect(reservations.create).toHaveBeenCalledWith({ scheduled_date: '2026-10-15', starts_at: '09:30', ends_at: '10:30', title: 'Reunião da sala', details: null });
  await userEvent.click(screen.getByRole('button', { name: 'Mês seguinte' }));
  expect(await screen.findByRole('region', { name: /Calendário de novembro de 2026/i })).toBeVisible();
  expect(reservations.list).toHaveBeenCalledWith('2026-11');
});

it('blocks a start sooner than 30 minutes and hides the form without permission', async () => {
  vi.mocked(reservations.list).mockResolvedValue([{ ...item, ends_at: '07:30', action: 'Finalizado' }]);
  const { rerender } = render(<RoomReservations canWrite={false} now={now} />);
  await userEvent.click(await screen.findByRole('button', { name: /15 de outubro de 2026, 1 reserva/ }));
  expect(screen.getByText('Ação: Finalizado')).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Reservar' })).not.toBeInTheDocument();
  rerender(<RoomReservations canWrite now={now} />);
  await userEvent.click(screen.getByRole('button', { name: /15 de outubro de 2026, 1 reserva/ }));
  await userEvent.type(screen.getByLabelText('Título'), 'Agora');
  await userEvent.type(screen.getByLabelText('Início'), '08:20');
  await userEvent.type(screen.getByLabelText('Fim'), '09:20');
  await userEvent.click(screen.getByRole('button', { name: 'Reservar' }));
  expect(screen.getByText('A reserva precisa começar pelo menos 30 minutos após o horário atual.')).toBeVisible();
  expect(reservations.create).not.toHaveBeenCalled();
});
