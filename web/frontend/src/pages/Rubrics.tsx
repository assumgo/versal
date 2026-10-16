import { useCallback, useState, type FormEvent } from 'react';
import type { Company } from '../api/companies';
import type { ChartAccount } from '../api/chartAccounts';
import { rubrics, type Rubric, type RubricInput } from '../api/rubrics';
import { flagText, normalizeAccount, type ListQuery } from '../api/accounting';
import { errorMessage } from '../api/client';
import { AccountPicker } from '../components/AccountPicker';
import { Alert } from '../components/Alert';
import { CatalogPagination } from '../components/CatalogPagination';
import { DataTable } from '../components/DataTable';
import { LoadingState } from '../components/LoadingState';
import { useCatalogPage } from '../components/useCatalogPage';

export function Rubrics({ company, canWrite }: { company: Company | null; canWrite: boolean }) {
  if (!company) return <><h1>Rubricas</h1><Alert>Selecione uma empresa.</Alert></>;
  return <RubricCatalog key={`${company.id}:${company.status}:${canWrite}`} company={company} canWrite={canWrite && company.status === 'Ativa'} />;
}
function RubricCatalog({ company, canWrite }: { company: Company; canWrite: boolean }) {
  const [status, setStatus] = useState('');
  const load = useCallback((query: ListQuery) => rubrics.list(company.id, { ...query, status: status || undefined }), [company.id, status]);
  const catalog = useCatalogPage(load);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<Rubric | 'new' | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  async function save(input: Partial<RubricInput>) {
    if (!canWrite || busy || !editing) return;
    setBusy(true); catalog.setError(''); setNotice('');
    try {
      if (editing === 'new') await rubrics.create(company.id, input as RubricInput);
      else await rubrics.update(company.id, editing.id, input);
      if (catalog.alive.current) { setEditing(null); setNotice('Registro salvo.'); catalog.reload(); }
    } catch (error) { if (catalog.alive.current) catalog.setError(errorMessage(error)); }
    finally { if (catalog.alive.current) setBusy(false); }
  }
  return <><div className="page-heading"><h1>Rubricas</h1>{canWrite && <button disabled={busy} onClick={() => { setEditing('new'); setNotice(''); }}>Nova rubrica</button>}</div><Alert>{company.status === 'Ativa' ? `Rubricas de ${company.razao ?? company.id}, válidas para todas as competências.` : 'Empresa inativa: disponível somente para consulta.'}</Alert>
    {catalog.error && <Alert variant="error">{catalog.error}</Alert>}{notice && <Alert variant="success">{notice}</Alert>}
    {editing && canWrite && <RubricForm key={editing === 'new' ? 'new' : editing.id} companyId={company.id} row={editing === 'new' ? null : editing} busy={busy} onSave={save} onCancel={() => setEditing(null)} />}
    <form className="catalog-controls" onSubmit={event => { event.preventDefault(); catalog.search(search); }}><label>Pesquisar rubricas<input value={search} onChange={event => setSearch(event.target.value)} placeholder="Código ou descrição" /></label><label>Filtrar status<select value={status} disabled={busy} onChange={event => { setStatus(event.target.value); catalog.setOffset(0); }}><option value="">Todos</option><option value="Ativa">Ativa</option><option value="Inativa">Inativa</option></select></label><button type="submit" disabled={catalog.loading || busy}>Pesquisar</button></form>
    {catalog.loading ? <LoadingState /> : <section className="panel"><DataTable caption="Rubricas cadastradas" rows={catalog.page.items} rowKey={row => row.id} columns={[
      { key: 'id', title: 'ID', render: row => row.id }, { key: 'codigo', title: 'Código', render: row => row.codigo ?? '—' },
      { key: 'descricao', title: 'Descrição', render: row => row.descricao ?? '—' }, { key: 'tipo', title: 'Tipo', render: row => row.tipo ?? 'Não informado' },
      { key: 'debito', title: 'Débito', render: row => row.conta_debito ?? '—' }, { key: 'dcc', title: 'Déb. CC', render: row => flagText(row.debito_gera_cc) }, { key: 'dcor', title: 'Déb. COR', render: row => flagText(row.debito_gera_cor) },
      { key: 'credito', title: 'Crédito', render: row => row.conta_credito ?? '—' }, { key: 'ccc', title: 'Créd. CC', render: row => flagText(row.credito_gera_cc) }, { key: 'ccor', title: 'Créd. COR', render: row => flagText(row.credito_gera_cor) },
      { key: 'hid', title: 'Código histórico', render: row => row.historico_id ?? '—' }, { key: 'historico', title: 'Histórico', render: row => row.historico ?? '—' }, { key: 'status', title: 'Status', render: row => row.status ?? 'Não informado' },
      ...(canWrite ? [{ key: 'actions', title: 'Ações', render: (row: Rubric) => <button type="button" className="secondary" disabled={busy} aria-label={`Editar rubrica ${row.id}`} onClick={() => { setEditing(row); setNotice(''); }}>Editar</button> }] : []),
    ]} /><CatalogPagination total={catalog.page.total} offset={catalog.offset} limit={catalog.limit} busy={catalog.loading || busy} onOffsetChange={catalog.setOffset} onLimitChange={catalog.setLimit} /></section>}
    {catalog.error && <button className="secondary" disabled={busy || catalog.loading} onClick={catalog.reload}>Tentar novamente</button>}
  </>;
}
const defaults = { codigo: '', descricao: '', tipo: 'P', conta_debito: '', conta_credito: '', historico_id: '001000182', historico: '', status: 'Ativa', debito_gera_cc: '1', debito_gera_cor: '1', credito_gera_cc: '1', credito_gera_cor: '1' };
type Values = typeof defaults;
function RubricForm({ companyId, row, busy, onSave, onCancel }: { companyId: number; row: Rubric | null; busy: boolean; onSave: (input: Partial<RubricInput>) => Promise<void>; onCancel: () => void }) {
  const initial = row ? Object.fromEntries(Object.keys(defaults).map(key => [key, String(row[key as keyof Rubric] ?? '')])) as Values : defaults;
  const [values, setValues] = useState<Values>(initial);
  const [debit, setDebit] = useState<ChartAccount | null>(null);
  const [credit, setCredit] = useState<ChartAccount | null>(null);
  function field(key: keyof Values, value: string) { setValues(old => ({ ...old, [key]: value })); }
  const changed = (Object.keys(values) as (keyof Values)[]).filter(key => values[key] !== initial[key]);
  const invalidCode = (['conta_debito', 'conta_credito'] as const).some(key => (!row || changed.includes(key)) && values[key].trim() && !normalizeAccount(values[key]));
  function submit(event: FormEvent) {
    event.preventDefault();
    if (busy || invalidCode) return;
    const keys = row ? changed : Object.keys(values) as (keyof Values)[];
    const input = Object.fromEntries(keys.map(key => [key, key.includes('_gera_') ? Number(values[key]) : values[key]])) as Partial<RubricInput>;
    void onSave(input);
  }
  function side(name: 'debito' | 'credito', label: string, account: ChartAccount | null, resolved: (account: ChartAccount | null) => void) {
    const cc = `${name}_gera_cc` as keyof Values, cor = `${name}_gera_cor` as keyof Values;
    const previewCC = account ? account.utiliza_cc : null, previewCOR = account ? account.gera_cor : null;
    const validAccount = account && (previewCC === 0 || previewCC === 1) && (previewCOR === 0 || previewCOR === 1);
    const divergent = row && validAccount && (String(previewCC) !== initial[cc] || String(previewCOR) !== initial[cor]);
    const choice = (key: keyof Values, text: string, preview: number | null) => {
      const value = account ? (preview === 0 || preview === 1 ? String(preview) : '') : values[key];
      return <label>{text}<select value={value} disabled={!!account} onChange={event => field(key, event.target.value)}>{!['0', '1'].includes(value) && <option value={value}>Não informado</option>}<option value="1">Sim</option><option value="0">Não</option></select></label>;
    };
    return <fieldset className="rubric-side"><legend>{label}</legend><AccountPicker companyId={companyId} label={`Conta ${name === 'debito' ? 'débito' : 'crédito'}`} value={values[`conta_${name}`]} onChange={value => field(`conta_${name}`, value)} onResolved={resolved} disabled={busy} />{choice(cc, 'Gera centro de custo', previewCC)}{choice(cor, 'Gera correntista', previewCOR)}
      {account ? <p className="catalog-hint">Ao salvar, prevalecem as opções da conta cadastrada, como no desktop.</p> : <p className="catalog-hint">Sem conta correspondente no plano, serão mantidas as opções manuais.</p>}
      {divergent && <p className="catalog-hint">As opções salvas diferem do plano: CC {flagText(row[name === 'debito' ? 'debito_gera_cc' : 'credito_gera_cc'])}, COR {flagText(row[name === 'debito' ? 'debito_gera_cor' : 'credito_gera_cor'])}. Ao salvar, serão usadas as opções da conta acima.</p>}
      {account && !validAccount && <Alert variant="error">Corrija as opções CC/COR desta conta no plano antes de salvar a rubrica.</Alert>}
    </fieldset>;
  }
  return <section className="panel catalog-editor"><h2>{row ? 'Editar rubrica' : 'Nova rubrica'}</h2><form onSubmit={submit}><fieldset disabled={busy} className="catalog-form"><label>Código da rubrica<input required={!row || changed.includes('codigo')} value={values.codigo} onChange={event => field('codigo', event.target.value)} /></label><label>Descrição<input required={!row || changed.includes('descricao')} value={values.descricao} onChange={event => field('descricao', event.target.value)} /></label><label>Tipo da rubrica<select value={values.tipo} onChange={event => field('tipo', event.target.value)}>{!['P', 'D', 'E'].includes(values.tipo) && <option value={values.tipo}>{values.tipo || 'Não informado'}</option>}<option value="P">P — Provento</option><option value="D">D — Desconto</option><option value="E">E — Encargo</option></select></label><label>Status da rubrica<select value={values.status} onChange={event => field('status', event.target.value)}>{!['Ativa', 'Inativa'].includes(values.status) && <option value={values.status}>{values.status || 'Não informado'}</option>}<option value="Ativa">Ativa</option><option value="Inativa">Inativa</option></select></label>
    {side('debito', 'Débito', debit, setDebit)}{side('credito', 'Crédito', credit, setCredit)}
    <label>Código do histórico<input aria-label="Código do histórico" value={values.historico_id} onChange={event => field('historico_id', event.target.value)} /><span className="catalog-hint">Formatado com nove dígitos ao salvar; vazio usa 001000182.</span></label><label>Histórico<textarea aria-label="Histórico" value={values.historico} maxLength={200} onChange={event => field('historico', event.target.value.slice(0, 200))} /><span className="catalog-hint">Até 200 caracteres ao alterar; um histórico legado não editado será preservado.</span></label>
    {invalidCode && <Alert variant="error">Selecione uma conta da pesquisa ou informe um código com dígitos.</Alert>}
    <div className="actions"><button type="submit" disabled={busy || !!invalidCode || (!!row && !changed.length)}>Salvar</button><button type="button" className="secondary" onClick={onCancel}>Cancelar</button></div></fieldset></form></section>;
}
