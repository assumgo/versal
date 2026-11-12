import { useState, type FormEvent } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { ThemeToggle } from '../components/ThemeToggle';
import { IconMicrosoft } from '../components/icons';

export function Login() {
  const auth = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from || '/';
  const [email, setEmail] = useState('usuario@versalagro.com.br');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  if (!auth.loading && auth.user) {
    return <Navigate to={from} replace />;
  }

  async function handleMicrosoft() {
    setError('');
    setBusy(true);
    try {
      await auth.loginWithMicrosoft();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao autenticar com Microsoft.');
      setBusy(false);
    }
  }

  async function handleDevLogin(event: FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await auth.loginDev(email);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível entrar.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-theme">
        <ThemeToggle />
      </div>

      <div className="login-card">
        <div className="login-logo">
          <img src="/logo1.png" alt="Versal Agro Contabilidade" />
        </div>
        <h1>Alocação de Recursos</h1>
        <p className="subtitle">Entre com a identidade Microsoft 365 / Active Directory da equipe.</p>

        {error && (
          <div className="login-error" role="alert">
            {error}
          </div>
        )}

        <div className="login-actions">
          <button
            type="button"
            className="btn ms-btn"
            onClick={() => void handleMicrosoft()}
            disabled={busy}
          >
            <IconMicrosoft />
            Entrar com Microsoft 365
          </button>
        </div>

        {auth.allowDevLogin && (
          <form className="login-form" onSubmit={(event) => void handleDevLogin(event)} style={{ marginTop: '1.2rem' }}>
            <div className="field">
              <label htmlFor="dev-email">E-mail (modo desenvolvimento)</label>
              <input
                id="dev-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                autoComplete="username"
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              Entrar localmente
            </button>
            <p className="login-hint">
              {auth.azureConfigured
                ? 'Em produção, use apenas o botão Microsoft 365 / AD.'
                : 'Azure AD ainda não configurado. Defina VITE_AZURE_CLIENT_ID e VITE_AZURE_TENANT_ID.'}
            </p>
          </form>
        )}
      </div>

      <div className="powered">Powered by Versal Agro</div>
    </div>
  );
}
