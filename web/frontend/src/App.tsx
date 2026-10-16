import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Alert } from './components/Alert';
import { Header } from './components/Header';
import { Sidebar, type Page } from './components/Sidebar';
import { Login } from './pages/Login';
import { AuthProvider, useAuth } from './auth/AuthProvider';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { companies, type Company } from './api/companies';
import { errorMessage } from './api/client';
import { LoadingState } from './components/LoadingState';
import { Companies } from './pages/Companies';
import { Employees } from './pages/Employees';

type ShellProps = { company: string; competence: string; activePage: Page; onNavigate: (page: Page) => void; children: ReactNode; context?: (menu: ReactNode) => ReactNode };
export function AppShell({ company, competence, activePage, onNavigate, children, context }: ShellProps) {
  const [open, setOpen] = useState(false);
  const shell = useRef<HTMLDivElement>(null);
  const wasOpen = useRef(false);
  const close = () => setOpen(false);
  useEffect(() => {
    if (!open) {
      if (wasOpen.current) shell.current?.querySelector<HTMLButtonElement>('.menu-trigger')?.focus();
      wasOpen.current = false;
      return;
    }
    wasOpen.current = true;
    const desktop = window.matchMedia('(min-width: 901px)');
    const handleViewport = () => { if (desktop.matches) setOpen(false); };
    desktop.addEventListener('change', handleViewport);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    shell.current?.querySelector<HTMLButtonElement>('.drawer-close')?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close();
      if (event.key !== 'Tab') return;
      const buttons = shell.current?.querySelectorAll<HTMLButtonElement>('.sidebar button');
      if (!buttons?.length) return;
      const first = buttons[0], last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener('keydown', handleKey);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener('keydown', handleKey); desktop.removeEventListener('change', handleViewport); };
  }, [open]);
  return <div className="app-shell" ref={shell}><a className="skip-link" href="#page-content">Ir para o conteúdo</a>
    {open && <button className="drawer-backdrop" aria-label="Fechar menu pelo fundo" tabIndex={-1} onClick={close} />}
    <Sidebar company={company} activePage={activePage} open={open} onClose={close} onNavigate={page => { onNavigate(page); close(); }} />
    <div className="workspace" inert={open || undefined}>{context ? context(<button className="menu-trigger" aria-label="Abrir menu" aria-controls="sidebar" aria-expanded={open} onClick={() => setOpen(true)}>☰</button>) : <Header company={company} competence={competence} menuOpen={open} onOpenMenu={() => setOpen(true)} />}<main id="page-content" tabIndex={-1}>{children}</main></div>
  </div>;
}
const paths: Record<string, Page> = { '/': 'Dashboard', '/empresas': 'Empresas', '/colaboradores': 'Colaboradores' };
function SessionApp() {
  const auth = useAuth();
  const [path, setPath] = useState(window.location.pathname);
  const returnTo = useRef(path === '/login' ? '/' : path);
  const [items, setItems] = useState<Company[]>([]);
  const [selected, setSelected] = useState('');
  const [competence, setCompetence] = useState(() => { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`; });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [revision, setRevision] = useState(0);
  const [extraPage, setExtraPage] = useState<Page | null>(null);
  function navigate(next: string) { window.history.pushState({}, '', next); setPath(next); setExtraPage(null); }
  useEffect(() => { const pop = () => { setPath(window.location.pathname); setExtraPage(null); }; window.addEventListener('popstate', pop); return () => window.removeEventListener('popstate', pop); }, []);
  useEffect(() => {
    if (!auth.user) { setItems([]); setSelected(''); return; }
    let active = true; setLoading(true); setError('');
    companies.list().then(data => { if (active) { setItems(data); setSelected(old => data.some(item => String(item.id) === old) ? old : String(data[0]?.id ?? '')); } }).catch(error => { if (active) { setItems([]); setSelected(''); setError(errorMessage(error)); } }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [auth.user, revision]);
  if (auth.loading) return <LoadingState />;
  if (path === '/login') return auth.user ? <LoginRedirect onRedirect={() => navigate(returnTo.current)} /> : <Login onSuccess={() => navigate(returnTo.current)} />;
  const company = items.find(item => String(item.id) === selected) ?? null;
  const page = extraPage ?? paths[path] ?? 'Dashboard';
  return <ProtectedRoute onLogin={() => { returnTo.current = path; navigate('/login'); }}><AppShell company={company?.razao ?? 'Nenhuma empresa'} competence={competence} activePage={page} onNavigate={page => { const next = Object.entries(paths).find(([, value]) => value === page); if (next) navigate(next[0]); else setExtraPage(page); }} context={menu => <header className="top-header">{menu}<div className="context-field"><label htmlFor="active-company">Empresa ativa</label><select id="active-company" value={selected} disabled={loading} onChange={event => setSelected(event.target.value)}><option value="">Selecione uma empresa</option>{items.map(item => <option key={item.id} value={item.id}>{item.razao ?? item.id}</option>)}</select></div><div className="context-field competence"><label htmlFor="active-competence">Competência ativa</label><input id="active-competence" type="month" value={competence} onChange={event => setCompetence(event.target.value)} /></div><button className="secondary" onClick={() => { void auth.logout().catch(error => setError(errorMessage(error))); }}>Sair</button></header>}>
    {error && <><Alert variant="error">{error}</Alert><button onClick={() => setRevision(value => value + 1)}>Tentar novamente</button></>}
    {page === 'Empresas' ? <Companies canWrite={auth.user?.role === 'Administrador'} onChanged={() => setRevision(value => value + 1)} /> : page === 'Colaboradores' ? loading ? <LoadingState /> : <Employees key={selected} company={company} canWrite={['Administrador', 'Operador'].includes(auth.user?.role ?? '')} /> : <><h1>{page}</h1><Alert>{page === 'Dashboard' ? 'Selecione uma empresa e acesse os cadastros de empresas e colaboradores. Os indicadores de folha estarão disponíveis em uma próxima etapa.' : 'Este módulo será disponibilizado em uma próxima etapa.'}</Alert></>}
  </AppShell></ProtectedRoute>;
}
function LoginRedirect({ onRedirect }: { onRedirect: () => void }) { useEffect(onRedirect, []); return null; }
export default function App() { return <AuthProvider><SessionApp /></AuthProvider>; }
