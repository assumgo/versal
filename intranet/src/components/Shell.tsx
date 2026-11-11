import { useEffect, useRef, useState, type ReactNode } from 'react';
import { directory, groupsLabel, initials } from '../auth/directory';
import { useSession } from '../auth/SessionProvider';
import { Link, useRoute } from './RouteProvider';

export function Shell({ children }: { children: ReactNode }) {
  const { user, signIn, signOut } = useSession();
  const { go } = useRoute();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    function onPointer(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', onPointer);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onPointer);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);
  if (!user) return null;
  return (
    <div className="app">
      <a className="skip" href="#conteudo">Ir para o conteúdo</a>
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            <img src="/assets/logo_versal_agro.png" alt="Versal Agro Contabilidade" />
          </Link>
          <div className="account" ref={menuRef}>
            <button
              type="button"
              className="account-button"
              aria-label={`Conta: ${user.name}`}
              aria-haspopup="menu"
              aria-expanded={open}
              onClick={() => setOpen(value => !value)}
            >
              <span className="avatar" aria-hidden="true">{initials(user.name)}</span>
              <span className="account-text">
                <strong>{user.name}</strong>
                <small>{groupsLabel(user.groups)}</small>
              </span>
            </button>
            {open && (
              <div className="account-menu" role="menu">
                <p>Pré-visualização de acesso</p>
                {directory.map(person => (
                  <button
                    key={person.id}
                    type="button"
                    role="menuitem"
                    aria-current={person.id === user.id ? 'true' : undefined}
                    onClick={() => { signIn(person.id); setOpen(false); }}
                  >
                    <strong>{person.name}</strong>
                    <small>{groupsLabel(person.groups)}</small>
                  </button>
                ))}
                <button type="button" className="sign-out" role="menuitem" onClick={() => { signOut(); setOpen(false); go('/'); }}>Sair</button>
              </div>
            )}
          </div>
        </div>
      </header>
      <main id="conteudo" className="content">{children}</main>
      <footer className="footer">
        <div className="content footer-inner">
          <span>Versal Agro Contabilidade</span>
          <Link to="/comunicados">Ver todos os comunicados</Link>
        </div>
      </footer>
    </div>
  );
}
