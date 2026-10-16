import { useCallback, useState, type FormEvent } from 'react';
import type { Company } from '../api/companies';
import { financeParams, type FinanceParam, type FinanceParamInput } from '../api/financeParams';
import type { ListQuery } from '../api/accounting';
import { errorMessage } from '../api/client';
import { Alert } from '../components/Alert';
import { CatalogPagination } from '../components/CatalogPagination';
import { DataTable } from '../components/DataTable';
import { LoadingState } from '../components/LoadingState';
import { useCatalogPage } from '../components/useCatalogPage';

const fields = [['tipo', 'Tipo'], ['documento_id', 'ID tipo documento'], ['parceiro_cpf_cnpj', 'CPF/CNPJ parceiro'], ['codigo_parceiro_siagri', 'Código parceiro Siagri'], ['conta_contrapartida', 'Conta contrapartida'], ['centro_custo', 'Centro custo guia'], ['vencimento_dia', 'Dia vencimento'], ['historico', 'Histórico']] as const;

export function FinanceParams({ company, canWrite }: { company: Company | null; canWrite: boolean }) {
  if (!company) return <><h1>Parametrização financeira</h1><Alert>Selecione uma empresa.</Alert></>;
  return <FinanceCatalog key={`${company.id}:${company.status}:${canWrite}`} company={company} canWrite={canWrite && company.status === 'Ativa'} />;
}
function FinanceCatalog({ company, canWrite }: { company: Company; canWrite: boolean }) {
  const load = useCallback(({ offset, limit }: ListQuery) => financeParams.list(company.id, { offset, limit }), [company.id]);
  const catalog = useCatalogPage(load);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  async function save(input: FinanceParamInput) {
    if (!canWrite || busy) return;
    setBusy(true); setNotice(''); catalog.setError('');
    try {
      await financeParams.create(company.id, input);
      if (catalog.alive.current) { setEditing(false); setNotice('Registro salvo.'); catalog.reload(); }
    } catch (error) { if (catalog.alive.current) catalog.setError(errorMessage(error)); }
    finally { if (catalog.alive.current) setBusy(false); }
  }
  return <><div className="page-heading"><h1>Parametrização financeira</h1>{canWrite && <button disabled={busy} onClick={() => { setEditing(true); setNotice(''); }}>Novo parâmetro</button>}</div>
    <Alert>{company.status === 'Ativa' ? `Parâmetros de ${company.razao ?? company.id}, válidos para todas as competências.` : 'Empresa inativa: disponível somente para consulta.'}</Alert>
    {catalog.error && <Alert variant="error">{catalog.error}</Alert>}{notice && <Alert variant="success">{notice}</Alert>}
    {editing && canWrite && <FinanceForm busy={busy} onSave={save} onCancel={() => setEditing(false)} />}
    {catalog.loading ? <LoadingState /> : <section className="panel"><DataTable<FinanceParam> caption="Parâmetros financeiros cadastrados" rows={catalog.page.items} rowKey={row => row.id} columns={fields.map(([key, title]) => ({ key, title, render: row => row[key] ?? '—' }))} />
      <CatalogPagination total={catalog.page.total} offset={catalog.offset} limit={catalog.limit} busy={catalog.loading || busy} onOffsetChange={catalog.setOffset} onLimitChange={catalog.setLimit} /></section>}
    {catalog.error && <button className="secondary" disabled={busy || catalog.loading} onClick={catalog.reload}>Tentar novamente</button>}
  </>;
}
function FinanceForm({ busy, onSave, onCancel }: { busy: boolean; onSave: (input: FinanceParamInput) => Promise<void>; onCancel: () => void }) {
  const [values, setValues] = useState({ tipo: '', documento_id: '', parceiro_cpf_cnpj: '', codigo_parceiro_siagri: '', conta_contrapartida: '', centro_custo: '', vencimento_dia: '1', historico: '' });
  function submit(event: FormEvent) { event.preventDefault(); if (!busy) void onSave({ ...values, vencimento_dia: Number(values.vencimento_dia) }); }
  return <section className="panel catalog-editor"><h2>Novo parâmetro financeiro</h2><form onSubmit={submit}><fieldset className="catalog-form" disabled={busy}>
    {fields.map(([key, title]) => <label key={key}>{title}<input value={values[key]} onChange={event => setValues(old => ({ ...old, [key]: event.target.value }))} type={key === 'vencimento_dia' ? 'number' : 'text'} min={key === 'vencimento_dia' ? 1 : undefined} max={key === 'vencimento_dia' ? 31 : undefined} step={key === 'vencimento_dia' ? 1 : undefined} required={key === 'vencimento_dia'} placeholder={key === 'tipo' ? 'Ex.: LIQUIDO_FOLHA, INSS, FGTS, IRRF, OUTROS' : undefined} /></label>)}
    <div className="actions"><button type="submit" disabled={busy}>Salvar parâmetro financeiro</button><button type="button" className="secondary" onClick={onCancel}>Cancelar</button></div>
  </fieldset></form></section>;
}
