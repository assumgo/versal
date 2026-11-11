import { groupsLabel } from '../auth/directory';
import { useSession } from '../auth/SessionProvider';
import { Link } from '../components/RouteProvider';
import { findShortcut } from '../shortcuts/catalog';
import { ShortcutGlyph } from '../shortcuts/icons';
import { canAccess, safeHref } from '../shortcuts/access';

export function ShortcutGate({ id }: { id: string }) {
  const { user } = useSession();
  const shortcut = findShortcut(id);
  if (!user) return null;
  if (!shortcut) {
    return (
      <section className="gate">
        <h1>Atalho não encontrado</h1>
        <p>Esse endereço não corresponde a um site da página inicial.</p>
        <Link to="/" className="primary">Voltar à página inicial</Link>
      </section>
    );
  }
  const allowed = canAccess(user.groups, shortcut);
  const href = allowed ? safeHref(shortcut.href) : null;
  return (
    <section className="gate">
      <span className="shortcut-icon"><ShortcutGlyph name={shortcut.icon} /></span>
      <h1>{shortcut.label}</h1>
      <p>{shortcut.hint}</p>
      {allowed ? (
        <>
          <p className="meta">Liberado para {groupsLabel(shortcut.groups)}.</p>
          {href ? (
            <a className="primary" href={href} target="_blank" rel="noreferrer">Abrir site</a>
          ) : (
            <p>Defina uma URL http(s) para este atalho no catálogo.</p>
          )}
        </>
      ) : (
        <p>Este site pede um grupo que não está no seu acesso. Grupos previstos: {groupsLabel(shortcut.groups)}.</p>
      )}
      <Link to="/">Voltar à página inicial</Link>
    </section>
  );
}
