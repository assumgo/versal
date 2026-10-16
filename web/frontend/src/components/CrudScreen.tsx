import { useEffect, useState, type FormEvent } from 'react';
import { DataTable } from './DataTable';
import { FormField } from './FormField';
import { Alert } from './Alert';
import { LoadingState } from './LoadingState';
import { errorMessage } from '../api/client';
type Field = { key: string; label: string; required?: boolean };
type RecordRow = { id: number; [key: string]: string | number | null };
type Props<T extends RecordRow> = { title: string; caption: string; createLabel: string; fields: Field[]; statuses: string[]; canWrite: boolean; load: () => Promise<T[]>; save: (data: Record<string, string>, id?: number) => Promise<unknown>; remove: (id: number) => Promise<unknown>; removeLabel: string; onChanged?: () => void };
export function CrudScreen<T extends RecordRow>({ title, caption, createLabel, fields, statuses, canWrite, load, save, remove, removeLabel, onChanged }: Props<T>) {
  const [rows, setRows] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [revision, setRevision] = useState(0);
  const [editing, setEditing] = useState<T | 'new' | null>(null);
  const [pending, setPending] = useState<T | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true; setLoading(true); setError(''); setRows([]);
    load().then(data => { if (active) setRows(data); }).catch(error => { if (active) setError(errorMessage(error)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [load, revision]);
  async function mutate(action: () => Promise<unknown>, message: string) {
    setBusy(true); setError(''); setNotice('');
    try { await action(); setEditing(null); setPending(null); setNotice(message); setRevision(value => value + 1); onChanged?.(); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!canWrite || busy) return;
    const data = Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string, string>;
    void mutate(() => save(data, editing && editing !== 'new' ? editing.id : undefined), 'Registro salvo.');
  }
  return <><div className="page-heading"><h1>{title}</h1>{canWrite && <button disabled={busy} onClick={() => { setEditing('new'); setPending(null); }}>{createLabel}</button>}</div>
    {error && <Alert variant="error">{error}</Alert>}{notice && <Alert variant="success">{notice}</Alert>}
    {canWrite && editing && <section className="panel"><h2>{editing === 'new' ? createLabel : 'Editar registro'}</h2><form onSubmit={submit} key={editing === 'new' ? 'new' : editing.id}><fieldset disabled={busy}>{fields.map(field => <FormField key={field.key} label={field.label} name={field.key} required={field.required} defaultValue={editing === 'new' ? '' : String(editing[field.key] ?? '')} />)}<div className="form-field"><label htmlFor="record-status">Status</label><select id="record-status" name="status" defaultValue={editing === 'new' ? statuses[0] : String(editing.status ?? statuses[0])}>{statuses.map(status => <option key={status}>{status}</option>)}</select></div><div className="actions"><button type="submit">Salvar</button><button type="button" className="secondary" onClick={() => setEditing(null)}>Cancelar</button></div></fieldset></form></section>}
    {canWrite && pending && <section className="panel" role="region" aria-label="Confirmar operação"><h2>{removeLabel} registro?</h2><p>{removeLabel === 'Inativar' ? 'O histórico da empresa será preservado.' : 'A exclusão do cadastro é permanente.'}</p><div className="actions"><button disabled={busy} onClick={() => void mutate(() => remove(pending.id), 'Operação concluída.')}>Confirmar</button><button disabled={busy} className="secondary" onClick={() => setPending(null)}>Cancelar</button></div></section>}
    {loading ? <LoadingState /> : error && !editing && !pending ? <button onClick={() => setRevision(value => value + 1)}>Tentar novamente</button> : <section className="panel"><DataTable caption={caption} rows={rows} rowKey={row => row.id} columns={[{ key: 'id', title: 'ID', render: row => row.id }, ...fields.map(field => ({ key: field.key, title: field.label, render: (row: T) => row[field.key] ?? '—' })), { key: 'status', title: 'Status', render: row => row.status ?? '—' }, ...(canWrite ? [{ key: 'actions', title: 'Ações', render: (row: T) => <div className="actions"><button disabled={busy} onClick={() => { setEditing(row); setPending(null); }}>Editar</button><button disabled={busy} className="secondary" onClick={() => { setPending(row); setEditing(null); }}>{removeLabel}</button></div> }] : [])]} /></section>}
  </>;
}
