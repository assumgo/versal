import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { DataTable } from '../components/DataTable';
import { FormField } from '../components/FormField';
import { Alert } from '../components/Alert';
import { LoadingState } from '../components/LoadingState';

it('associates field validation feedback with its input', () => {
  render(<FormField label="CNPJ" error="Informe um CNPJ válido." />);
  expect(screen.getByLabelText('CNPJ')).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByLabelText('CNPJ')).toHaveAccessibleDescription('Informe um CNPJ válido.');
});
it('preserves table headers when there are no records', () => {
  render(<DataTable<{ id: number }> caption="Registros" columns={[{ key: 'id', title: 'ID', render: row => row.id }]} rows={[]} rowKey={row => row.id} />);
  expect(screen.getByRole('columnheader', { name: 'ID' })).toBeVisible();
  expect(screen.getByRole('cell', { name: 'Nenhum registro encontrado.' })).toBeVisible();
});
it('announces errors and loading states', () => {
  render(<><Alert variant="error">Não foi possível carregar.</Alert><LoadingState /></>);
  expect(screen.getByRole('alert')).toHaveTextContent('Não foi possível carregar.');
  expect(screen.getByRole('status')).toHaveTextContent('Carregando…');
});
