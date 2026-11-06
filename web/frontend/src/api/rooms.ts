import { request } from './client';

export type Room = { id: number; name: string };

export const rooms = {
  list: () => request<Room[]>('/rooms'),
};
