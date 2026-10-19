import { useState } from 'react';
import type { PayrollPreviewResponse, PreviewEmployee, PreviewRubric } from '../api/payrollPreview';
import { Alert } from './Alert';
import { CatalogPagination } from './CatalogPagination';
import { DataTable, type Column } from './DataTable';

const rubricColumns: Column<PreviewRubric>[] = [
  ['codigo', 'Código'], ['descricao', 'Descrição'], ['referencia', 'Referência'], ['valor', 'Valor'], ['tipo', 'Tipo'],
].map(([key, title]) => ({ key, title, render: row => row[key as keyof PreviewRubric] || '—' }));
export function PayrollPreviewResult({ preview }: { preview: PayrollPreviewResponse }) {
  const [selected, setSelected] = useState(0);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(25);
  const [rubricOffset, setRubricOffset] = useState(0);
  const [rubricLimit, setRubricLimit] = useState(25);
  const people = preview.statement.colaboradores;
  const person = people[selected];
  const columns: Column<PreviewEmployee>[] = [
    { key: 'matricula', title: 'Matrícula', render: row => row.matricula || '—' },
    { key: 'nome', title: 'Colaborador', render: row => <button type="button" className="secondary" onClick={() => { setSelected(people.indexOf(row)); setRubricOffset(0); }}>{row.nome || 'Sem nome'}</button> },
    ...[['cpf', 'CPF'], ['situacao', 'Situação'], ['cargo', 'Cargo'], ['centro_custo', 'Centro de custo'], ['liquido', 'Líquido']].map(([key, title]) => ({ key, title, render: (row: PreviewEmployee) => row[key as keyof PreviewEmployee] as string || '—' })),
    { key: 'rubricas', title: 'Rubricas', render: row => row.rubricas.length },
  ];
  return <section className="preview-result" aria-label="Resultado da prévia">
    <Alert variant={preview.status === 'blocked' ? 'error' : undefined}>{preview.status === 'blocked' ? 'Prévia bloqueada: confira as divergências.' : 'Prévia pronta para conferência.'}</Alert>
    {preview.issues.map(issue => <Alert key={issue.code} variant={issue.severity === 'blocking' ? 'error' : undefined}>{issue.message}</Alert>)}
    <p>Arquivo: {preview.filename} · Contexto consultado: empresa {preview.company_id}, {preview.requested_competence}</p>
    <p>Empresa detectada: {preview.statement.empresa.razao || 'Não identificada'} · CNPJ: {preview.statement.empresa.cnpj || 'Não identificado'} · Competência detectada: {preview.statement.competencia || 'Não identificada'}</p>
    <dl className="preview-summary">
      <dt>Colaboradores</dt><dd>{preview.summary.employees}</dd><dt>Rubricas</dt><dd>{preview.summary.rubrics}</dd>
      <dt>Proventos (P)</dt><dd>{preview.summary.totals_by_type.P}</dd><dt>Descontos (D)</dt><dd>{preview.summary.totals_by_type.D}</dd>
      <dt>Encargos (E)</dt><dd>{preview.summary.totals_by_type.E}</dd><dt>Líquidos informados</dt><dd>{preview.summary.net_total}</dd>
    </dl>
    <section className="panel" aria-label="Lista de colaboradores">
      <DataTable caption="Colaboradores da prévia" columns={columns} rows={people.slice(offset, offset + limit)} rowKey={(_, index) => offset + index} />
      <CatalogPagination total={people.length} offset={offset} limit={limit} busy={false} onOffsetChange={setOffset} onLimitChange={value => { setLimit(value); setOffset(0); }} />
    </section>
    {person && <section className="panel" aria-label="Lista de rubricas"><h2>Rubricas de {person.nome || 'colaborador sem nome'}</h2>
      <DataTable caption="Rubricas do colaborador" columns={rubricColumns} rows={person.rubricas.slice(rubricOffset, rubricOffset + rubricLimit)} rowKey={(_, index) => rubricOffset + index} />
      <CatalogPagination total={person.rubricas.length} offset={rubricOffset} limit={rubricLimit} busy={false} onOffsetChange={setRubricOffset} onLimitChange={value => { setRubricLimit(value); setRubricOffset(0); }} />
    </section>}
  </section>;
}
