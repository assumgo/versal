import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { PayrollImportPreview } from '../pages/PayrollImportPreview';
import { payrollPreview } from '../api/payrollPreview';
import { payrollImports } from '../api/payrollImports';
import { ApiError } from '../api/client';
import { previewCompany, previewResult } from './payrollPreviewFixtures';
vi.mock('../api/payrollPreview', () => ({ payrollPreview: { generate: vi.fn() } }));
vi.mock('../api/payrollImports', () => ({ payrollImports: { confirm: vi.fn(), list: vi.fn() } }));
const generate = vi.mocked(payrollPreview.generate);
const confirmImport = vi.mocked(payrollImports.confirm);
const listImports = vi.mocked(payrollImports.list);
const props = { company: previewCompany, competence: '2026-09', canPreview: true };
const file = () => new File(['synthetic'], 'input.pdf', { type: 'application/pdf' });
async function submit() {
  const selected = file();
  await userEvent.upload(screen.getByLabelText('Extrato Mensal'), selected);
  await userEvent.click(screen.getByRole('button', { name: 'Gerar prévia' }));
  return selected;
}
beforeEach(() => {
  generate.mockReset(); generate.mockResolvedValue(previewResult);
  confirmImport.mockReset(); confirmImport.mockResolvedValue({
    import_id: 42, company_id: 1, competence: '09/2026', filename: 'input.pdf', size_bytes: 50,
    sha256: 'a'.repeat(64), imported_at: '2026-10-19T12:00:00Z', employees: 2, rubrics: 4,
    totals_by_type: { P: '5000.00', D: '500.00', E: '0' }, net_total: '4500.00',
  });
  listImports.mockReset().mockResolvedValue({ items: [], offset: 0, limit: 50, total: 0 });
});
it('shows preview, exact server totals, all fields and duplicate rubrics', async () => {
  render(<PayrollImportPreview {...props} />);
  await submit();
  expect(generate.mock.calls[0].slice(0, 3)).toEqual([1, expect.any(File), '09/2026']);
  expect(await screen.findByText(previewResult.summary.net_total)).toBeVisible();
  expect(screen.getByText('Prévia pronta para conferência.')).toBeVisible();
  expect(screen.getByRole('table', { name: 'Colaboradores da prévia' })).toBeVisible();
  expect(screen.getAllByText('SALARIO BASE')).toHaveLength(2);
  expect(localStorage.length).toBe(0);
  expect(sessionStorage.length).toBe(0);
});
it('shows blocking context issues without hiding parsed contents', async () => {
  generate.mockResolvedValue({ ...previewResult, status: 'blocked', issues: [{ code: 'company_cnpj_mismatch', severity: 'blocking', message: 'O CNPJ difere da empresa selecionada.' }] });
  render(<PayrollImportPreview {...props} />);
  await submit();
  expect(await screen.findByText('Prévia bloqueada: confira as divergências.')).toBeVisible();
  expect(screen.getByText('O CNPJ difere da empresa selecionada.')).toBeVisible();
  expect(screen.getByText('Ana Sintética', { exact: true })).toBeVisible();
});
it('handles missing company, denied role and inactive company without sending', () => {
  const { rerender } = render(<PayrollImportPreview {...props} company={null} />);
  expect(screen.getByText('Selecione uma empresa.')).toBeVisible();
  rerender(<PayrollImportPreview {...props} canPreview={false} />);
  expect(screen.getByText('Sem permissão para consultar importações.')).toBeVisible();
  rerender(<PayrollImportPreview {...props} company={{ ...previewCompany, status: 'Inativa' }} />);
  expect(screen.getByText('Empresa inativa.')).toBeVisible();
  expect(generate).not.toHaveBeenCalled();
});
it('keeps selected file on error and supports retry', async () => {
  generate.mockRejectedValueOnce(new Error('Arquivo ilegível.'));
  render(<PayrollImportPreview {...props} />);
  await submit();
  expect(await screen.findByText('Arquivo ilegível.')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Gerar prévia' }));
  expect(await screen.findByText('Prévia pronta para conferência.')).toBeVisible();
});
it.each([{ company: { ...previewCompany, id: 2 } }, { competence: '2026-10' }, { company: { ...previewCompany, status: 'Inativa' } }, { canPreview: false }])('discards late results after context changes %j', async changes => {
  let resolve!: (value: typeof previewResult) => void;
  generate.mockReturnValueOnce(new Promise(done => { resolve = done; }));
  const { rerender } = render(<PayrollImportPreview {...props} />);
  await submit();
  expect(screen.getByRole('button', { name: 'Gerando prévia…' })).toBeDisabled();
  rerender(<PayrollImportPreview {...props} {...changes} />);
  await act(async () => resolve(previewResult));
  expect(screen.queryByText(previewResult.summary.net_total)).not.toBeInTheDocument();
  const input = screen.queryByLabelText('Extrato Mensal') as HTMLInputElement | null;
  if (input) expect(input.files).toHaveLength(0);
});
it('clears old results when choosing another file and paginates locally without changing totals', async () => {
  const long = structuredClone(previewResult);
  long.statement.colaboradores = Array.from({ length: 26 }, (_, i) => ({ ...long.statement.colaboradores[0], nome: `Pessoa ${i}`, rubricas: Array.from({ length: 26 }, () => long.statement.colaboradores[0].rubricas[0]) }));
  generate.mockResolvedValue(long);
  render(<PayrollImportPreview {...props} />);
  await submit();
  const people = await screen.findByRole('region', { name: 'Lista de colaboradores' });
  expect(within(people).getByText('1–25 de 26 registros')).toBeVisible();
  await userEvent.click(within(people).getByRole('button', { name: 'Próxima' }));
  expect(within(people).getByText('26–26 de 26 registros')).toBeVisible();
  await userEvent.selectOptions(within(people).getByLabelText('Registros por página'), '50');
  expect(within(people).getByText('1–26 de 26 registros')).toBeVisible();
  const rubrics = screen.getByRole('region', { name: 'Lista de rubricas' });
  await userEvent.selectOptions(within(rubrics).getByLabelText('Registros por página'), '100');
  expect(within(rubrics).getByText('1–26 de 26 registros')).toBeVisible();
  expect(screen.getByText(long.summary.net_total)).toBeVisible();
  await userEvent.upload(screen.getByLabelText('Extrato Mensal'), file());
  await waitFor(() => expect(screen.queryByText(long.summary.net_total)).not.toBeInTheDocument());
});

it('rejects invalid files and invalid competence before sending', async () => {
  const user = userEvent.setup({ applyAccept: false });
  const { rerender } = render(<PayrollImportPreview {...props} />);
  const input = screen.getByLabelText('Extrato Mensal');
  await user.upload(input, new File(['data'], 'input.exe'));
  expect(screen.getByText('Envie PDF, XLS ou XLSX.')).toBeVisible();
  await user.upload(input, new File([], 'empty.pdf'));
  expect(screen.getByText('O arquivo está vazio.')).toBeVisible();
  await user.upload(input, new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'large.pdf'));
  expect(screen.getByText('O arquivo excede 10 MiB.')).toBeVisible();
  rerender(<PayrollImportPreview {...props} competence="2026-13" />);
  await user.upload(screen.getByLabelText('Extrato Mensal'), file());
  expect(screen.getByRole('button', { name: 'Gerar prévia' })).toBeDisabled();
  expect(generate).not.toHaveBeenCalled();
});
it('discards a pending result after another file or unmount', async () => {
  let resolve!: (value: typeof previewResult) => void;
  generate.mockReturnValueOnce(new Promise(done => { resolve = done; }));
  const { unmount } = render(<PayrollImportPreview {...props} />);
  await submit();
  const signal = generate.mock.calls[0][3]?.signal;
  await userEvent.upload(screen.getByLabelText('Extrato Mensal'), new File(['next'], 'next.pdf'));
  expect(signal?.aborted).toBe(true);
  await act(async () => resolve(previewResult));
  expect(screen.queryByText(previewResult.summary.net_total)).not.toBeInTheDocument();
  generate.mockImplementationOnce((_company, _file, _competence, options) => new Promise((_resolve, reject) => options?.signal?.addEventListener('abort', () => reject(new Error('aborted')))));
  await userEvent.click(screen.getByRole('button', { name: 'Gerar prévia' }));
  const latest = generate.mock.calls[1][3]?.signal;
  unmount();
  await act(async () => {});
  expect(latest?.aborted).toBe(true);
});

it('confirms the exact ready preview and clears it after persisted success', async () => {
  render(<PayrollImportPreview {...props} />);
  const selected = await submit();
  const confirm = await screen.findByRole('button', { name: 'Confirmar importação' });
  expect(confirm).toBeEnabled();
  await userEvent.click(confirm);
  expect(confirmImport.mock.calls[0].slice(0, 4)).toEqual([1, selected, '09/2026', previewResult.sha256]);
  expect(await screen.findByText(/Importação #42 concluída/)).toBeVisible();
  expect(screen.queryByText('Prévia pronta para conferência.')).not.toBeInTheDocument();
});

it('keeps a ready preview after a duplicate conflict and explains the conflict', async () => {
  confirmImport.mockRejectedValueOnce(new ApiError(409, 'Esta competência já possui uma importação.'));
  render(<PayrollImportPreview {...props} />);
  await submit();
  await userEvent.click(await screen.findByRole('button', { name: 'Confirmar importação' }));
  expect(await screen.findByText('Esta competência já possui uma importação.')).toBeVisible();
  expect(screen.getByText('Prévia pronta para conferência.')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Confirmar importação' })).toBeEnabled();
});

it('allows retrying a transient confirmation error with the same selected file', async () => {
  confirmImport.mockRejectedValueOnce(new ApiError(503, 'Leitores ocupados.'));
  render(<PayrollImportPreview {...props} />);
  await submit();
  await userEvent.click(await screen.findByRole('button', { name: 'Confirmar importação' }));
  expect(await screen.findByText('Leitores ocupados.')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar importação' }));
  expect(await screen.findByText(/Importação #42 concluída/)).toBeVisible();
  expect(confirmImport).toHaveBeenCalledTimes(2);
  expect(confirmImport.mock.calls[0][1]).toBe(confirmImport.mock.calls[1][1]);
});

it('prevents repeat confirmation while the request is pending', async () => {
  let resolve!: (value: Awaited<ReturnType<typeof payrollImports.confirm>>) => void;
  confirmImport.mockReturnValueOnce(new Promise(done => { resolve = done; }));
  render(<PayrollImportPreview {...props} />);
  await submit();
  const button = await screen.findByRole('button', { name: 'Confirmar importação' });
  await userEvent.click(button);
  expect(screen.getByRole('button', { name: 'Salvando importação…' })).toBeDisabled();
  expect(confirmImport).toHaveBeenCalledTimes(1);
  await act(async () => resolve({
    import_id: 42, company_id: 1, competence: '09/2026', filename: 'input.pdf', size_bytes: 50,
    sha256: 'a'.repeat(64), imported_at: '2026-10-19T12:00:00Z', employees: 2, rubrics: 4,
    totals_by_type: { P: '5000.00', D: '500.00', E: '0' }, net_total: '4500.00',
  }));
});

it('lets read-only Consulta users see metadata history without an upload form', async () => {
  listImports.mockResolvedValueOnce({ items: [{
    import_id: 12, company_id: 1, competence: '09/2026', filename: 'input.pdf', status: 'Concluída',
    imported_at: '2026-10-19T12:00:00Z', size_bytes: 50, sha256: 'a'.repeat(64), employees: 2, rubrics: 4,
  }], offset: 0, limit: 50, total: 1 });
  render(<PayrollImportPreview {...props} canPreview={false} canRead />);
  expect(await screen.findByText('09/2026')).toBeVisible();
  expect(screen.getByText('input.pdf')).toBeVisible();
  expect(screen.queryByLabelText('Extrato Mensal')).not.toBeInTheDocument();
  expect(screen.queryByText('Ana Sintética')).not.toBeInTheDocument();
});

it('paginates the server history for read-only users', async () => {
  const row = { import_id: 12, company_id: 1, competence: '09/2026', filename: 'input.pdf', status: 'Concluída',
    imported_at: '2026-10-19T12:00:00Z', size_bytes: 50, sha256: 'a'.repeat(64), employees: 2, rubrics: 4 };
  listImports.mockResolvedValueOnce({ items: [row], offset: 0, limit: 50, total: 51 })
    .mockResolvedValueOnce({ items: [{ ...row, import_id: 11 }], offset: 50, limit: 50, total: 51 });
  render(<PayrollImportPreview {...props} canPreview={false} canRead />);
  expect(await screen.findByText('input.pdf')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }));
  await waitFor(() => expect(listImports).toHaveBeenLastCalledWith(1, { offset: 50, limit: 50 }, { signal: expect.any(AbortSignal) }));
  expect(listImports).toHaveBeenCalledTimes(2);
});
