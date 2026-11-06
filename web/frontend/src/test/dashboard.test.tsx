import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { Dashboard } from '../pages/Dashboard';

it('keeps payroll indicators out of the room reservation', () => {
  render(<Dashboard />);
  expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  expect(screen.queryByText('Seg')).not.toBeInTheDocument();
});
