import { expect, it } from 'vitest';
import { dayRange, saoPauloToIso } from './time';

it('converts a São Paulo local time to UTC', () => {
  expect(saoPauloToIso('2026-11-04T09:00')).toBe('2026-11-04T12:00:00.000Z');
  expect(saoPauloToIso('2026-11-04T10:30')).toBe('2026-11-04T13:30:00.000Z');
});

it('builds a half-open day range in São Paulo', () => {
  expect(dayRange('2026-11-04')).toEqual({
    from: '2026-11-04T03:00:00.000Z',
    to: '2026-11-05T03:00:00.000Z',
  });
});
