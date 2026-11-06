import { useEffect, useState, type FormEvent } from 'react';
import { users, type Account } from '../api/users';
import { Alert } from '../components/Alert';
import { DataTable } from '../components/DataTable';
import { FormField } from '../components/FormField';
import { LoadingState } from '../components/LoadingState';
import { errorMessage } from '../api/client';

const roles = ['Administrador', 'Contador', 'Operador', 'Consulta'];
type Pending = { account: Account; action: 'inactivate' | 'reactivate' | 'delete' };
const confirmCopy: Record<Pending['action'], { title: string; body: string; done: string }> = {
  inactivate: { title: 'Inativar usuário?', body: 'O usuário deixa de acessar o sistema. O cadastro e o histórico permanecem.', done: 'Usuário inativado.' },
  reactivate: { title: 'Reativar usuário?', body: 'O usuário volta a poder acessar o sistema.', done: 'Usuário reativado.' },
  delete: { title: 'Excluir usuário?', body: 'A exclusão é definitiva. O histórico permanece, sem o vínculo com este usuário.', done: 'Usuário excluído.' },
};

export function Users({ canWrite }: { canWrite: boolean }) {
  const [rows, setRows] = useState<Account[]>([]);
  const [loading, setLoading] = useState(canWrite);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [revision, setRevision] = useState(0);
  const [editing, setEditing] = useState<Account | null>(null);
  const [role, setRole] = useState('Operador');
  const [pending, setPending] = useState<Pending | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!canWrite) return;
    let active = true;
    setLoading(true); setError(''); setRows([]);
    users.list().then(data => { if (active) setRows(data); }).catch(reason => { if (active) setError(errorMessage(reason)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [canWrite, revision]);
  if (!canWrite) return <><h1>Usuários</h1><Alert variant="error">Sem permissão para acessar este recurso.</Alert></>;
  function openEdit(account: Account) { setEditing(account); setRole(account.role); setPending(null); }
  async function mutate(action: () => Promise<unknown>, message: string) {
    setBusy(true); setError(''); setNotice('');
    try { await action(); setEditing(null); setPending(null); setNotice(message); setRevision(value => value + 1); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setBusy(false); }
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing || busy) return;
    const data = new FormData(event.currentTarget);
    const name = String(data.get('name') ?? '').trim();
    const login = String(data.get('login') ?? '');
    const changes: { name?: string; login?: string; role?: string } = {};
    if (name !== (editing.name ?? '')) changes.name = name;
    if (login !== (editing.login ?? '')) changes.login = login;
    if (role !== editing.role) changes.role = role;
    if (!Object.keys(changes).length) { setEditing(null); setNotice('Registro salvo.'); return; }
    void mutate(() => users.update(editing.id, changes), 'Registro salvo.');
  }
  function confirm() {
    if (!pending || busy) return;
    const { account, action } = pending;
    const request = action === 'delete' ? () => users.remove(account.id) : action === 'inactivate' ? () => users.inactivate(account.id) : () => users.update(account.id, { is_active: true });
    void mutate(request, confirmCopy[action].done);
  }
  return <><div className="page-heading"><h1>Usuários</h1></div>
    {error && <Alert variant="error">{error}</Alert>}{notice && <Alert variant="success">{notice}</Alert>}
    {editing && <section className="panel user-panel"><h2>Editar usuário</h2><form className="user-form" onSubmit={submit}><fieldset disabled={busy}>
      <FormField label="Nome" name="name" defaultValue={editing.name ?? ''} maxLength={120} />
      <FormField label="Login" name="login" defaultValue={editing.login ?? ''} required minLength={3} maxLength={80} />
      <FormField label="E-mail" name="email" defaultValue={editing.email} readOnly />
      <div className="form-field"><label htmlFor="user-role">Papel</label><select id="user-role" value={role} onChange={event => setRole(event.target.value)}>{roles.map(item => <option key={item}>{item}</option>)}</select></div>
      <label className="check-line" htmlFor="user-admin"><input id="user-admin" type="checkbox" checked={role === 'Administrador'} onChange={event => setRole(event.target.checked ? 'Administrador' : role === 'Administrador' ? 'Operador' : role)} />Administrador</label>
      <div className="actions"><button type="submit">Salvar</button><button type="button" className="secondary" onClick={() => setEditing(null)}>Cancelar</button></div>
    </fieldset></form></section>}
    {pending && <section className="panel user-panel" role="region" aria-label="Confirmar operação"><div className="user-form"><h2>{confirmCopy[pending.action].title}</h2><p>{confirmCopy[pending.action].body}</p><div className="actions"><button disabled={busy} onClick={confirm}>Confirmar</button><button disabled={busy} className="secondary" onClick={() => setPending(null)}>Cancelar</button></div></div></section>}
    {loading ? <LoadingState /> : error && !editing && !pending ? <button onClick={() => setRevision(value => value + 1)}>Tentar novamente</button> : <section className="panel"><DataTable caption="Usuários cadastrados" rows={rows} rowKey={row => row.id} columns={[
      { key: 'name', title: 'Nome', render: row => row.name ?? '—' },
      { key: 'login', title: 'Login', render: row => row.login ?? '—' },
      { key: 'email', title: 'E-mail', render: row => row.email },
      { key: 'role', title: 'Papel', render: row => row.role },
      { key: 'status', title: 'Situação', render: row => row.is_active ? 'Ativo' : 'Inativo' },
      { key: 'actions', title: 'Ações', render: row => <div className="actions"><button disabled={busy} onClick={() => openEdit(row)}>Editar</button>{row.is_active ? <button disabled={busy} className="secondary" onClick={() => { setPending({ account: row, action: 'inactivate' }); setEditing(null); }}>Inativar</button> : <button disabled={busy} className="secondary" onClick={() => { setPending({ account: row, action: 'reactivate' }); setEditing(null); }}>Reativar</button>}<button disabled={busy} className="secondary" onClick={() => { setPending({ account: row, action: 'delete' }); setEditing(null); }}>Excluir</button></div> },
    ]} /></section>}
  </>;
}
