import { useState, type FormEvent } from 'react';
import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';
import { useAuth } from '../auth/AuthProvider';
import { errorMessage } from '../api/client';
export function Login({ onSuccess }: { onSuccess: () => void }) {
  const auth = useAuth();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true); setError('');
    try { await auth.login(String(data.get('login')), String(data.get('password'))); onSuccess(); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <main className="login-page"><section className="panel login-card"><img src="/assets/logo_versal_agro.png" alt="Versal Agro Contabilidade" /><h1>Acessar o Integrador Folha TXT</h1>{error && <Alert variant="error">{error}</Alert>}<form onSubmit={submit}><FormField label="Login" name="login" autoComplete="username" required minLength={3} maxLength={80} /><FormField label="Senha" name="password" type="password" autoComplete="current-password" required /><button type="submit" disabled={busy}>{busy ? 'Entrando…' : 'Entrar'}</button></form></section></main>;
}
