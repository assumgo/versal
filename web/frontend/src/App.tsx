import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Alert } from './components/Alert';
import { Header } from './components/Header';
import { Sidebar, type Page } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Companies } from './pages/Companies';
import { Employees } from './pages/Employees';

type ShellProps = { company: string; competence: string; activePage: Page; onNavigate: (page: Page) => void; children: ReactNode };
export function AppShell({ company, competence, activePage, onNavigate, children }: ShellProps) {
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
    <div className="workspace" inert={open || undefined}><Header company={company} competence={competence} menuOpen={open} onOpenMenu={() => setOpen(true)} /><main id="page-content" tabIndex={-1}><Alert>Ambiente de demonstração · dados simulados, sem conexão com o banco operacional.</Alert>{children}</main></div>
  </div>;
}
export default function App() {
  const [page, setPage] = useState<Page>('Dashboard');
  return <AppShell company="Empresa Demonstração Ltda." competence="2026-10" activePage={page} onNavigate={setPage}>{page === 'Dashboard' ? <Dashboard /> : page === 'Empresas' ? <Companies /> : page === 'Colaboradores' ? <Employees /> : <><div className="page-heading"><h1>{page}</h1></div><Alert>Este módulo será disponibilizado em uma próxima etapa.</Alert></>}</AppShell>;
}
