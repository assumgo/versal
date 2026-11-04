import { useState, type FormEvent } from 'react';
import { errorMessage } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';

export function Login({ onSuccess }: { onSuccess: () => void }) {
  const auth = useAuth();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError('');
    try {
      await auth.login(String(data.get('email')), String(data.get('password')));
      onSuccess();
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }
  return <main className="login-page">
    <section className="panel login-card">
      <h1>Agenda de salas</h1>
      <p>Entre com o e-mail e a senha da sua conta.</p>
      {error && <Alert variant="error">{error}</Alert>}
      <form onSubmit={submit}>
        <FormField label="E-mail" name="email" type="email" autoComplete="username" required />
        <FormField label="Senha" name="password" type="password" autoComplete="current-password" required />
        <button type="submit" disabled={busy}>{busy ? 'Entrando…' : 'Entrar'}</button>
      </form>
    </section>
  </main>;
}
