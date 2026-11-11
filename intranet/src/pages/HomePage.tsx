import { bySource, type Announcement } from '../announcements/feed';
import { useSession } from '../auth/SessionProvider';
import { Link } from '../components/RouteProvider';
import { formatPublished, formatToday } from '../format';
import { shortcuts } from '../shortcuts/catalog';
import { ShortcutGlyph } from '../shortcuts/icons';
import { visibleShortcuts } from '../shortcuts/access';

export function HomePage() {
  const { user } = useSession();
  if (!user) return null;
  const available = visibleShortcuts(user.groups, shortcuts);
  return (
    <>
      <header className="intro">
        <h1>Página inicial</h1>
        <p>{formatToday()}</p>
      </header>
      <section className="block" aria-labelledby="atalhos-titulo">
        <div className="section-head">
          <h2 id="atalhos-titulo">Atalhos</h2>
        </div>
        {available.length === 0 ? (
          <p className="empty">Nenhum atalho disponível para o seu acesso.</p>
        ) : (
          <ul className="shortcut-grid">
            {available.map(shortcut => (
              <li key={shortcut.id}>
                <Link to={`/atalhos/${shortcut.id}`} className="shortcut">
                  <span className="shortcut-icon"><ShortcutGlyph name={shortcut.icon} /></span>
                  <span>
                    <strong>{shortcut.label}</strong>
                    <small>{shortcut.hint}</small>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
      <div className="boards">
        <AnnouncementPanel title="Comunicados" source="oficial" />
        <AnnouncementPanel title="Quadro do Teams" source="teams" />
      </div>
    </>
  );
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
