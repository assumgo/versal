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
  return { from: saoPauloToIso(`${date}T00:00`), to: saoPauloToIso(`${addDays(date, 1)}T00:00`) };
}

export function formatSlot(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: ZONE, day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso));
}
