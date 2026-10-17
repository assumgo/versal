import { useCallback, useEffect, useState } from 'react';
import type { Company } from '../api/companies';
import { accountingReview, type AccountingReviewRow } from '../api/accountingReview';
import type { ListQuery } from '../api/accounting';
import { errorMessage } from '../api/client';
import { Alert } from '../components/Alert';
import { CatalogPagination } from '../components/CatalogPagination';
import { DataTable, type Column } from '../components/DataTable';
import { LoadingState } from '../components/LoadingState';
import { useCatalogPage } from '../components/useCatalogPage';

const validCompetence = (value: string) => /^(0[1-9]|1[0-2])\/[0-9]{4}$/.test(value);
const fields = [['competencia', 'Comp.'], ['cpf', 'CPF'], ['nome', 'Colaborador'], ['codigo_verba', 'Verba'], ['verba', 'Descrição'], ['valor', 'Valor'], ['conta_debito', 'Débito'], ['debito_gera_cc', 'D CC'], ['debito_gera_cor', 'D COR'], ['conta_credito', 'Crédito'], ['credito_gera_cc', 'C CC'], ['credito_gera_cor', 'C COR'], ['historico_id', 'Histórico ID'], ['historico', 'Histórico'], ['centro_custo', 'Centro custo'], ['correntista', 'Correntista'], ['fonte', 'Fonte']] as const;
const columns: Column<AccountingReviewRow>[] = fields.map(([key, title]) => ({ key, title, render: row => {
  const value = row[key];
  return typeof value === 'boolean' ? value ? 'Sim' : 'Não' : value ?? '—';
} }));

export function AccountingReview({ company }: { company: Company | null }) {
  if (!company) return <><h1>Parametrização contábil</h1><Alert>Selecione uma empresa.</Alert></>;
  return <ReviewContext key={`${company.id}:${company.status}`} company={company} />;
}
function ReviewContext({ company }: { company: Company }) {
  const [competences, setCompetences] = useState<string[]>([]);
  const [selected, setSelected] = useState('');
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    accountingReview.competences(company.id).then(values => {
      if (!active) return;
      setCompetences(values);
      setSelected(old => values.includes(old) && validCompetence(old) ? old : values.find(validCompetence) ?? values[0] ?? '');
    }).catch(error => { if (active) setError(errorMessage(error)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [company.id, revision]);
  return <><div className="page-heading"><h1>Parametrização contábil</h1><button disabled={loading} onClick={() => setRevision(value => value + 1)}>Atualizar conferência</button></div>
    <Alert>Conferência de {company.razao ?? company.id}: valores das importações, contas e histórico das rubricas, centro de custo e correntista dos colaboradores. Selecione a competência abaixo para consultar.</Alert>
    <div className="catalog-controls"><label>Competência da conferência<select aria-label="Competência da conferência" value={selected} disabled={loading || !competences.length} onChange={event => setSelected(event.target.value)}>
      {!competences.length && <option value="">Nenhuma competência</option>}{competences.map(value => <option key={value} value={value}>{value}</option>)}
    </select></label></div>
    {error && <><Alert variant="error">{error}</Alert><button className="secondary" onClick={() => setRevision(value => value + 1)}>Tentar novamente</button></>}
    {loading ? <LoadingState /> : error ? null : !competences.length ? <Alert>Nenhuma competência importada.</Alert> : !validCompetence(selected) ? <Alert>Selecione uma competência válida (MM/AAAA). As competências legadas não foram alteradas.</Alert> : <ReviewLines key={`${selected}:${revision}`} company={company.id} competence={selected} />}
  </>;
}
function ReviewLines({ company, competence }: { company: number; competence: string }) {
  const load = useCallback(({ offset, limit }: ListQuery) => accountingReview.list(company, { competence, offset, limit }), [company, competence]);
  const catalog = useCatalogPage(load);
  return <>{catalog.error && <><Alert variant="error">{catalog.error}</Alert><button className="secondary" disabled={catalog.loading} onClick={catalog.reload}>Tentar novamente</button></>}
    {catalog.loading ? <LoadingState /> : <section className="panel"><DataTable caption="Conferência contábil" rows={catalog.page.items} rowKey={row => row.id} columns={columns} />
      <CatalogPagination total={catalog.page.total} offset={catalog.offset} limit={catalog.limit} busy={catalog.loading} onOffsetChange={catalog.setOffset} onLimitChange={catalog.setLimit} /></section>}
  </>;
}
