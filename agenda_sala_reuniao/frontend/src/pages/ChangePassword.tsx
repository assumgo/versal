import { useState, type FormEvent } from 'react';
import { errorMessage } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';

export function ChangePassword() {
  const auth = useAuth();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const currentPassword = String(data.get('current_password'));
    const newPassword = String(data.get('new_password'));
    const confirmation = String(data.get('confirmation'));
    if (newPassword.length < 8) {
      setError('A nova senha precisa ter pelo menos 8 caracteres.');
      return;
    }
    if (newPassword !== confirmation) {
      setError('A confirmação da senha não confere.');
      return;
    }
    if (newPassword === currentPassword) {
      setError('A nova senha deve ser diferente da atual.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await auth.changePassword(currentPassword, newPassword);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return <main className="login-page">
    <section className="panel login-card">
      <h1>Defina uma nova senha</h1>
      <p>Este acesso exige uma senha própria. Depois da troca, a senha anterior deixa de valer.</p>
      {error && <Alert variant="error">{error}</Alert>}
      <form className="form-grid" onSubmit={submit}>
        <FormField label="Senha atual" name="current_password" type="password" autoComplete="current-password" required />
        <FormField label="Nova senha" name="new_password" type="password" autoComplete="new-password" required minLength={8} />
        <FormField label="Confirmar nova senha" name="confirmation" type="password" autoComplete="new-password" required minLength={8} />
        <div className="actions">
          <button type="button" className="secondary" onClick={() => { void auth.logout(); }}>Sair</button>
          <button type="submit" disabled={busy}>{busy ? 'Salvando…' : 'Salvar senha'}</button>
        </div>
      </form>
    </section>
  </main>;
}
