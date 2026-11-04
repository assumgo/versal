import { request } from './client';

export type Reservation = {
  id: number; room_id: number; room_name: string; user_id: number; user_name: string;
  title: string; starts_at: string; ends_at: string; mine: boolean;
};

export const listReservations = (from: string, to: string, roomId: string) => {
  const params = new URLSearchParams({ from, to });
  if (roomId) params.set('room_id', roomId);
  return request<Reservation[]>(`/reservations?${params}`);
};

export const createReservation = (body: { room_id: number; title: string; starts_at: string; ends_at: string }) => (
  request<Reservation>('/reservations', { method: 'POST', body: JSON.stringify(body) })
);

export const cancelReservation = (id: number) => request<void>(`/reservations/${id}`, { method: 'DELETE' });
