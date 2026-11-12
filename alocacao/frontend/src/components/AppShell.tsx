import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

type AppShellProps = {
  children: ReactNode;
  ctaLabel?: string;
  onCta?: () => void;
};

export function AppShell({ children, ctaLabel = '+ Nova alocação', onCta }: AppShellProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const shell = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const desktop = window.matchMedia('(min-width: 961px)');
    const handleViewport = () => {
      if (desktop.matches) setOpen(false);
    };
    desktop.addEventListener('change', handleViewport);
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = previous;
      document.removeEventListener('keydown', onKey);
      desktop.removeEventListener('change', handleViewport);
    };
  }, [open]);

  return (
    <div className="app-shell" ref={shell}>
      <a className="skip-link" href="#page-content">
        Ir para o conteúdo
      </a>
      {open && (
        <button
          type="button"
          className="drawer-backdrop"
          aria-label="Fechar menu pelo fundo"
          tabIndex={-1}
          onClick={() => setOpen(false)}
        />
      )}
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="workspace">
        <TopBar
          menuOpen={open}
          onOpenMenu={() => setOpen(true)}
          search={search}
          onSearch={setSearch}
          ctaLabel={ctaLabel}
          onCta={onCta}
        />
        <main id="page-content" className="content" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
