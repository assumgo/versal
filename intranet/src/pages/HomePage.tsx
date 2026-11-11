import { useEffect, useRef, useState } from 'react';
import { bySource, type Announcement } from '../announcements/feed';
import { isAdministrator } from '../auth/directory';
import { useSession } from '../auth/SessionProvider';
import { Link } from '../components/RouteProvider';
import { formatPublished, formatToday } from '../format';
import type { Shortcut } from '../shortcuts/catalog';
import { ShortcutGlyph } from '../shortcuts/icons';
import { canAccess, safeHref } from '../shortcuts/access';
import { addShortcut, listShortcuts, type ShortcutDraft } from '../shortcuts/store';
import { ShortcutForm } from './ShortcutForm';

export function HomePage() {
  const { user } = useSession();
  const [items, setItems] = useState(listShortcuts);
  const [creating, setCreating] = useState(false);
  const [blocked, setBlocked] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!blocked) return;
    closeRef.current?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setBlocked(null);
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [blocked]);

  function create(draft: ShortcutDraft) {
    const result = addShortcut(draft);
    if (!result.ok) return result.error;
    setItems(listShortcuts());
    return null;
  }

  function select(shortcut: Shortcut) {
    const href = safeHref(shortcut.href);
    if (user && canAccess(user.groups, shortcut) && href) {
      window.open(href, '_blank', 'noopener,noreferrer');
      return;
    }
    setBlocked(shortcut.label);
  }

  return (
    <>
      <header className="intro">
        <h1>Página inicial</h1>
        <p>{formatToday()}</p>
      </header>
      <div className="home-grid">
        <section className="panel panel-shortcuts" aria-labelledby="atalhos-titulo">
          <div className="section-head">
            <h2 id="atalhos-titulo">Atalhos</h2>
            {isAdministrator(user) && <button type="button" className="text-action" onClick={() => setCreating(true)}>Incluir atalho</button>}
          </div>
          <ul className="shortcut-grid">
            {items.map(shortcut => (
              <li key={shortcut.id}>
                <button type="button" className="shortcut" onClick={() => select(shortcut)}>
                  <span className="shortcut-icon"><ShortcutGlyph name={shortcut.icon} /></span>
                  <span>
                    <strong>{shortcut.label}</strong>
                    <small>{shortcut.hint || addressLabel(shortcut.href)}</small>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
        <div className="side-stack">
          <AnnouncementPanel title="Quadro do Teams" source="teams" />
          <AnnouncementPanel title="Comunicados" source="oficial" />
        </div>
      </div>
      {creating && <ShortcutForm onClose={() => setCreating(false)} onCreate={create} />}
      {blocked && (
        <div className="modal-backdrop" onMouseDown={() => setBlocked(null)}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="sem-permissao"
            onMouseDown={event => event.stopPropagation()}
          >
            <h2 id="sem-permissao">{blocked}</h2>
            <p>Você não tem permissão para acessar este local.</p>
            <button ref={closeRef} type="button" className="primary" onClick={() => setBlocked(null)}>Fechar</button>
          </div>
        </div>
      )}
    </>
  );
}

function addressLabel(href: string) {
  try { return new URL(href).host; } catch { return ''; }
}

function AnnouncementPanel({ title, source }: { title: string; source: Announcement['source'] }) {
  const items = bySource(source).slice(0, 3);
  const id = `${source}-titulo`;
  return (
    <section className={`panel panel-${source}`} aria-labelledby={id}>
      <div className="section-head">
        <h2 id={id}>{title}</h2>
        <Link to="/comunicados">Ver todos</Link>
      </div>
      <div className="feed">
        {items.map(item => (
          <article key={item.id}>
            <p className="meta">{formatPublished(item.publishedAt)} · {item.channel}</p>
            <h3>{item.title}</h3>
            <p>{item.summary}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
