import { useEffect, useState, type FormEvent } from 'react';
import type { User } from '../api/auth';
import { createUser, listUsers, requirePasswordChange } from '../api/users';
import { errorMessage } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';

export function Users() {
  const auth = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [admin, setAdmin] = useState(false);

  function load() {
    return listUsers().then(setUsers).catch(cause => setError(errorMessage(cause)));
  }
  useEffect(() => { if (auth.user?.is_admin) void load(); }, [auth.user]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await createUser({
        name: String(data.get('name')), email: String(data.get('email')),
        password: String(data.get('password')), is_admin: admin,
      });
      form.reset();
      setAdmin(false);
      setNotice('Conta criada. A pessoa troca a senha no primeiro acesso.');
      await load();
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function requireChange(user: User) {
    setPendingId(user.id);
    setError('');
    setNotice('');
    try {
      const updated = await requirePasswordChange(user.id);
      setUsers(current => current.map(item => item.id === updated.id ? updated : item));
      setNotice(`${updated.name} vai trocar a senha no próximo acesso.`);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setPendingId(null);
    }
  }

  if (!auth.user?.is_admin) return <Alert variant="error">Acesso restrito ao administrador.</Alert>;
  return <>
    <header className="page-heading">
      <h1>Usuários</h1>
      <p>Crie contas para quem vai consultar a agenda e reservar salas.</p>
    </header>
    {error && <Alert variant="error">{error}</Alert>}
    {notice && <Alert>{notice}</Alert>}
    <div className="split">
      <section className="panel">
        <div className="table-scroll">
          <table>
            <caption>Contas cadastradas</caption>
            <thead><tr><th>Nome</th><th>E-mail</th><th>Perfil</th><th>Acesso</th></tr></thead>
            <tbody>
              {users.map(user => <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>{user.is_admin ? 'Administrador' : 'Usuário'}</td>
                <td>{user.must_change_password
                  ? <span className="status-badge">Troca no próximo acesso</span>
                  : <div className="row-actions"><button type="button" className="secondary" disabled={pendingId === user.id} onClick={() => { void requireChange(user); }}>Exigir troca de senha</button></div>}
                </td>
              </tr>)}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel">
        <form className="form-grid" onSubmit={submit}>
          <h2>Nova conta</h2>
          <p>A senha informada vale só até o primeiro acesso.</p>
          <FormField label="Nome" name="name" required maxLength={120} />
          <FormField label="E-mail" name="email" type="email" autoComplete="off" required />
          <FormField label="Senha" name="password" type="password" autoComplete="new-password" required minLength={8} />
          <label className="check-field"><input type="checkbox" checked={admin} onChange={event => setAdmin(event.target.checked)} /> Administrador</label>
          <div className="actions"><button type="submit" disabled={busy}>{busy ? 'Salvando…' : 'Criar conta'}</button></div>
        </form>
      </section>
    </div>
  </>;
}
