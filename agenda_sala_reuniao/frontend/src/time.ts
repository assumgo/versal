export const ZONE = 'America/Sao_Paulo';

function offsetMinutes(instant: Date): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: ZONE, hourCycle: 'h23',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  }).formatToParts(instant);
  const map = Object.fromEntries(parts.filter(part => part.type !== 'literal').map(part => [part.type, part.value]));
  const asUtc = Date.UTC(Number(map.year), Number(map.month) - 1, Number(map.day), Number(map.hour), Number(map.minute), Number(map.second));
  return (asUtc - instant.getTime()) / 60000;
}

/** Interpret a datetime-local value as America/Sao_Paulo and return UTC ISO. */
export function saoPauloToIso(local: string): string {
  const normalized = local.length === 16 ? `${local}:00` : local;
  const [datePart, timePart] = normalized.split('T');
  const [year, month, day] = datePart.split('-').map(Number);
  const [hour, minute, second] = timePart.split(':').map(Number);
  const civil = Date.UTC(year, month - 1, day, hour, minute, second || 0);
  const first = new Date(civil - offsetMinutes(new Date(civil)) * 60000);
  return new Date(civil - offsetMinutes(first) * 60000).toISOString();
}

export function todayInSaoPaulo(now = new Date()): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: ZONE, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now);
  const map = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return `${map.year}-${map.month}-${map.day}`;
}

export function addDays(date: string, days: number): string {
  const [year, month, day] = date.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day + days)).toISOString().slice(0, 10);
}

export function dayRange(date: string): { from: string; to: string } {
  return periodRange(date, addDays(date, 1));
}

export function periodRange(startDate: string, endDate: string): { from: string; to: string } {
  return { from: saoPauloToIso(`${startDate}T00:00`), to: saoPauloToIso(`${endDate}T00:00`) };
}

/** Monday–Sunday week that contains the civil date, in America/Sao_Paulo. */
export function weekRange(date: string): { from: string; to: string; start: string } {
  const [year, month, day] = date.split('-').map(Number);
  const weekday = new Date(Date.UTC(year, month - 1, day)).getUTCDay();
  const start = addDays(date, weekday === 0 ? -6 : 1 - weekday);
  return { ...periodRange(start, addDays(start, 7)), start };
}

export function monthRange(date: string): { from: string; to: string; start: string } {
  const [year, month] = date.split('-').map(Number);
  const start = `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-01`;
  const next = month === 12 ? `${year + 1}-01-01` : `${year}-${String(month + 1).padStart(2, '0')}-01`;
  return { ...periodRange(start, next), start };
}

const slotFormat = new Intl.DateTimeFormat('pt-BR', {
  timeZone: ZONE, day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

export function formatSlot(iso: string): string {
  return slotFormat.format(new Date(iso));
}

export function formatCivilDay(date: string): string {
  const [year, month, day] = date.split('-').map(Number);
  return new Intl.DateTimeFormat('pt-BR', { day: 'numeric', month: 'long', timeZone: 'UTC' }).format(new Date(Date.UTC(year, month - 1, day)));
}

export function formatMonth(date: string): string {
  const [year, month, day] = date.split('-').map(Number);
  return new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(Date.UTC(year, month - 1, day)));
}

export const TIME_24H = /^([01]\d|2[0-3]):[0-5]\d$/;
