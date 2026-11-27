import { useState, type FormEvent } from 'react';
import { api, setToken, type User } from '../api';

export function Login({ onSuccess }: { onSuccess: (user: User) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError('');
    try {
      const result = await api<{ access_token: string; user: User }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }, false);
      setToken(result.access_token);
      onSuccess(result.user);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível entrar.');
    } finally {
      setPending(false);
    }
  }

  return <main className="login-screen" id="conteudo">
    <form className="login-card" onSubmit={submit}>
      <p className="eyebrow">Gestão de projetos</p>
      <h1>Entrar</h1>
      <p className="lede">Acompanhe cada projeto da abertura até a entrega.</p>
      {error && <p className="alert" role="alert">{error}</p>}
      <label htmlFor="email">E-mail</label>
      <input id="email" type="email" autoComplete="username" value={email} onChange={event => setEmail(event.target.value)} required />
      <label htmlFor="password">Senha</label>
      <input id="password" type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required />
      <button type="submit" disabled={pending}>{pending ? 'Entrando…' : 'Entrar'}</button>
    </form>
  </main>;
}
