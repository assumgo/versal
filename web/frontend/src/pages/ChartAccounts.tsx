import { useCallback, useState, type FormEvent } from 'react';
import type { Company } from '../api/companies';
import { chartAccounts, type ChartAccount, type ChartAccountInput, type ChartAccountUpdate } from '../api/chartAccounts';
import { flagText, type Flag, type ListQuery } from '../api/accounting';
import { errorMessage } from '../api/client';
import { Alert } from '../components/Alert';
import { CatalogPagination } from '../components/CatalogPagination';
import { DataTable } from '../components/DataTable';
import { LoadingState } from '../components/LoadingState';
import { useCatalogPage } from '../components/useCatalogPage';

export function ChartAccounts({ company, canWrite }: { company: Company | null; canWrite: boolean }) {
  if (!company) return <><h1>Plano de contas</h1><Alert>Selecione uma empresa.</Alert></>;
  return <AccountCatalog key={`${company.id}:${company.status}:${canWrite}`} company={company} canWrite={canWrite && company.status === 'Ativa'} />;
}
function AccountCatalog({ company, canWrite }: { company: Company; canWrite: boolean }) {
  const load = useCallback((query: ListQuery) => chartAccounts.list(company.id, query), [company.id]);
  const catalog = useCatalogPage(load);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<ChartAccount | 'new' | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  async function save(input: ChartAccountInput | ChartAccountUpdate) {
    if (!canWrite || busy || !editing) return;
    setBusy(true); setNotice(''); catalog.setError('');
    try {
      if (editing === 'new') await chartAccounts.create(company.id, input as ChartAccountInput);
      else await chartAccounts.update(company.id, editing.id, input);
      if (catalog.alive.current) { setEditing(null); setNotice('Registro salvo.'); catalog.reload(); }
    } catch (error) { if (catalog.alive.current) catalog.setError(errorMessage(error)); }
    finally { if (catalog.alive.current) setBusy(false); }
  }
  return <><div className="page-heading"><h1>Plano de contas</h1>{canWrite && <button disabled={busy} onClick={() => { setEditing('new'); setNotice(''); }}>Nova conta</button>}</div>
    <Alert>{company.status === 'Ativa' ? `Cadastros de ${company.razao ?? company.id}, válidos para todas as competências.` : 'Empresa inativa: disponível somente para consulta.'}</Alert>
    {catalog.error && <Alert variant="error">{catalog.error}</Alert>}{notice && <Alert variant="success">{notice}</Alert>}
    {editing && canWrite && <AccountForm key={editing === 'new' ? 'new' : editing.id} row={editing === 'new' ? null : editing} busy={busy} onSave={save} onCancel={() => setEditing(null)} />}
    <form className="catalog-controls" onSubmit={event => { event.preventDefault(); catalog.search(search); }}><label>Pesquisar contas<input value={search} onChange={event => setSearch(event.target.value)} placeholder="Conta ou descrição" /></label><button type="submit" disabled={catalog.loading || busy}>Pesquisar</button></form>
    {catalog.loading ? <LoadingState /> : <section className="panel"><DataTable caption="Contas cadastradas" rows={catalog.page.items} rowKey={row => row.id} columns={[
      { key: 'id', title: 'ID', render: row => row.id }, { key: 'conta', title: 'Conta', render: row => row.conta ?? '—' },
      { key: 'descricao', title: 'Descrição', render: row => row.descricao ?? '—' },
      { key: 'cc', title: 'Gera CC', render: row => flagText(row.utiliza_cc) },
      { key: 'tipo', title: 'Tipo de correntista', render: row => row.tipo_correntista ?? 'Não informado' },
      { key: 'cor', title: 'Gera COR', render: row => flagText(row.gera_cor) },
      ...(canWrite ? [{ key: 'actions', title: 'Ações', render: (row: ChartAccount) => <button className="secondary" disabled={busy} aria-label={`Editar conta ${row.id}`} onClick={() => { setEditing(row); setNotice(''); }}>Editar</button> }] : []),
    ]} /><CatalogPagination total={catalog.page.total} offset={catalog.offset} limit={catalog.limit} busy={catalog.loading || busy} onOffsetChange={catalog.setOffset} onLimitChange={catalog.setLimit} /></section>}
    {catalog.error && <button className="secondary" disabled={busy || catalog.loading} onClick={catalog.reload}>Tentar novamente</button>}
  </>;
}
function AccountForm({ row, busy, onSave, onCancel }: { row: ChartAccount | null; busy: boolean; onSave: (input: ChartAccountInput | ChartAccountUpdate) => Promise<void>; onCancel: () => void }) {
  const initial = { conta: row?.conta ?? '', descricao: row?.descricao ?? '', utiliza_cc: row?.utiliza_cc == null ? '' : String(row.utiliza_cc), tipo_correntista: row?.tipo_correntista ?? '' };
  const [values, setValues] = useState(row ? initial : { conta: '', descricao: '', utiliza_cc: '0', tipo_correntista: '9-Nenhum' });
  function field(key: keyof typeof values, value: string) { setValues(old => ({ ...old, [key]: value })); }
  const changed = Object.keys(values).filter(key => key !== 'conta' && values[key as keyof typeof values] !== initial[key as keyof typeof initial]);
  const cor = row && values.tipo_correntista === initial.tipo_correntista ? row.gera_cor : Number(values.tipo_correntista.trim().startsWith('2'));
  function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (!row) void onSave({ conta: values.conta, descricao: values.descricao, utiliza_cc: Number(values.utiliza_cc) as Flag, tipo_correntista: values.tipo_correntista });
    else void onSave(Object.fromEntries(changed.map(key => [key, key === 'utiliza_cc' ? Number(values.utiliza_cc) : values[key as keyof typeof values]])) as ChartAccountUpdate);
  }
  return <section className="panel"><h2>{row ? 'Editar conta' : 'Nova conta'}</h2><form onSubmit={submit}><fieldset disabled={busy} className="catalog-form"><label>Conta<input required={!row} disabled={!!row} value={values.conta} onChange={event => field('conta', event.target.value)} /></label><label>Descrição<input required={!row || changed.includes('descricao')} value={values.descricao} onChange={event => field('descricao', event.target.value)} /></label><label>Gera centro de custo<select value={values.utiliza_cc} onChange={event => field('utiliza_cc', event.target.value)}>{row && initial.utiliza_cc === '' && <option value="">Não informado</option>}<option value="1">Sim</option><option value="0">Não</option></select></label><label>Tipo de correntista<input list="account-partner-types" required={!row || changed.includes('tipo_correntista')} value={values.tipo_correntista} onChange={event => field('tipo_correntista', event.target.value)} /><datalist id="account-partner-types"><option value="2-Parceiro" /><option value="9-Nenhum" /></datalist></label><p>Gera correntista: <strong>{flagText(cor)}</strong></p><p className="catalog-hint">O código da conta permanece fixo após o cadastro. Alterar esta conta não sincroniza as rubricas automaticamente.</p><div className="actions"><button type="submit" disabled={busy || (!!row && !changed.length)}>Salvar</button><button type="button" className="secondary" onClick={onCancel}>Cancelar</button></div></fieldset></form></section>;
}
