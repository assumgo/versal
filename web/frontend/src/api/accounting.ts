export type Flag = 0 | 1;
export type Page<T> = { items: T[]; total: number; offset: number; limit: number };
export type ListQuery = { q: string; offset: number; limit: number };
export function queryString(query: object) {
  return new URLSearchParams(Object.entries(query).filter(([, value]) => value !== undefined).map(([key, value]) => [key, String(value)])).toString();
}
export function flagText(value: number | null) { return value === 1 ? 'Sim' : value === 0 ? 'Não' : 'Não informado'; }
export function normalizeAccount(value: string) { return value.trim().replace(/\.0$/, '').replace(/\D/g, ''); }
