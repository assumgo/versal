import { request } from './client';

export type Appointment = {
  id: number;
  company_id: number;
  scheduled_date: string;
  starts_at: string;
  title: string;
  details: string | null;
};
export type AppointmentInput = { scheduled_date: string; starts_at: string; title: string; details?: string | null };

export const appointments = {
  list: (companyId: number, month: string) => request<Appointment[]>(`/companies/${companyId}/appointments?month=${month}`),
  create: (companyId: number, data: AppointmentInput) => request<Appointment>(`/companies/${companyId}/appointments`, { method: 'POST', body: JSON.stringify(data) }),
};
