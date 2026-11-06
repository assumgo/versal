import { request } from './client';

export type Reservation = {
  id: number;
  scheduled_date: string;
  starts_at: string;
  ends_at: string;
  title: string;
  details: string | null;
  action: 'Agendada' | 'Finalizado';
};
export type ReservationInput = { scheduled_date: string; starts_at: string; ends_at: string; title: string; details?: string | null };

export const reservations = {
  list: (month: string) => request<Reservation[]>(`/reservations?month=${month}`),
  create: (data: ReservationInput) => request<Reservation>('/reservations', { method: 'POST', body: JSON.stringify(data) }),
};
