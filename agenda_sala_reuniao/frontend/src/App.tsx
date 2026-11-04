import { useEffect, useState, type ReactNode } from 'react';
import { errorMessage } from './api/client';
import { AuthProvider, useAuth } from './auth/AuthProvider';
import { Agenda } from './pages/Agenda';
import { Login } from './pages/Login';
import { Rooms } from './pages/Rooms';
import { Users } from './pages/Users';

const paths = { '/': 'Agenda', '/salas': 'Salas', '/usuarios': 'Usuários' } as const;
type Page = keyof typeof paths;

function Shell({ path, onNavigate, children }: { path: Page; onNavigate: (path: Page) => void; children: ReactNode }) {
  const auth = useAuth();
  const [error, setError] = useState('');
  const links = (Object.keys(paths) as Page[]).filter(item => item !== '/usuarios' || auth.user?.is_admin);
  return <div className="app-shell">
    <a className="skip-link" href="#page-content">Ir para o conteúdo</a>
    <header className="top-header">
      <strong className="brand-name">Agenda de salas</strong>
      <nav aria-label="Seções">
        {links.map(item => <button key={item} type="button" aria-current={item === path ? 'page' : undefined} onClick={() => onNavigate(item)}>{paths[item]}</button>)}
      </nav>
      <span className="user-name">{auth.user?.name}</span>
      <button type="button" className="secondary" onClick={() => { void auth.logout().catch(cause => setError(errorMessage(cause))); }}>Sair</button>
    </header>
    <main id="page-content">
      {error && <p role="alert">{error}</p>}
      {children}
    </main>
  </div>;
}

function SessionApp() {
  const auth = useAuth();
  const [path, setPath] = useState(window.location.pathname);
  function navigate(next: string) {
    window.history.pushState({}, '', next);
    setPath(next);
  }
  useEffect(() => {
    const pop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', pop);
    return () => window.removeEventListener('popstate', pop);
  }, []);
  if (auth.loading) return <p className="loading-state"><span className="spinner" aria-hidden="true" />Carregando…</p>;
  if (!auth.user) return <Login onSuccess={() => navigate('/')} />;
  const current = (path in paths ? path : '/') as Page;
  const page = current === '/salas' ? <Rooms /> : current === '/usuarios' ? <Users /> : <Agenda />;
  return <Shell path={current} onNavigate={navigate}>{page}</Shell>;
}

export default function App() {
  return <AuthProvider><SessionApp /></AuthProvider>;
}
