import { expect, it } from 'vitest';
import { dayRange, formatSlot, monthRange, saoPauloToIso, weekRange } from './time';

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

it('formats hours on a 24-hour clock', () => {
  expect(formatSlot('2026-11-04T12:00:00.000Z')).toMatch(/09:00/);
  expect(formatSlot('2026-11-05T01:30:00.000Z')).toMatch(/22:30/);
  expect(formatSlot('2026-11-05T01:30:00.000Z')).not.toMatch(/AM|PM/);
});

it('covers the Monday week and the calendar month', () => {
  expect(weekRange('2026-11-04').start).toBe('2026-11-02');
  expect(weekRange('2026-11-01').start).toBe('2026-10-26');
  expect(monthRange('2026-11-04')).toMatchObject({
    start: '2026-11-01',
    from: '2026-11-01T03:00:00.000Z',
    to: '2026-12-01T03:00:00.000Z',
  });
});
