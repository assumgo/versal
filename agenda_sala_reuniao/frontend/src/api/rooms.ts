import { request } from './client';

export type Room = { id: number; name: string; location: string; capacity: number; is_active: boolean };
export type RoomInput = { name: string; location: string; capacity: number; is_active: boolean };

export const listRooms = () => request<Room[]>('/rooms');
export const createRoom = (body: RoomInput) => request<Room>('/rooms', { method: 'POST', body: JSON.stringify(body) });
export const updateRoom = (id: number, body: RoomInput) => request<Room>(`/rooms/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
