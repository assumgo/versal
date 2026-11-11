import { bySource, type Announcement } from '../announcements/feed';
import { Link } from '../components/RouteProvider';
import { formatPublished } from '../format';

export function AnnouncementsPage() {
  return (
    <>
      <header className="intro">
        <h1>Comunicados</h1>
        <p>Publicações gerais e o quadro do canal Comunicados.</p>
      </header>
      <div className="boards">
        <FullList title="Comunicados" source="oficial" />
        <FullList title="Quadro do Teams" source="teams" />
      </div>
      <p className="back-link"><Link to="/">Voltar à página inicial</Link></p>
    </>
  );
}

function FullList({ title, source }: { title: string; source: Announcement['source'] }) {
  const id = `lista-${source}`;
  return (
    <section className={`panel panel-${source}`} aria-labelledby={id}>
      <div className="section-head"><h2 id={id}>{title}</h2></div>
      <div className="feed">
        {bySource(source).map(item => (
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
