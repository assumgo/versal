import type { ReactNode } from 'react';
import type { ProjectContext, User } from './api';
import { eventText, formatDate, formatWhen, type ActivityEvent } from './format';
import { badgeFor, statusLabel } from './labels';
import { navigate } from './router';

export function AppLink({ href, className, children }: { href: string; className?: string; children: ReactNode }) {
  return <a className={className} href={href} onClick={event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
    event.preventDefault();
    navigate(href);
  }}>{children}</a>;
}

export function Shell({ user, onLogout, children }: { user: User; onLogout: () => void; children: ReactNode }) {
  return <div className="app">
    <a className="skip" href="#conteudo">Ir para o conteúdo</a>
    <header className="topbar">
      <AppLink href="/projects" className="brand">Gestão</AppLink>
      <p className="who">{user.name}</p>
      <button type="button" className="ghost" onClick={onLogout}>Sair</button>
    </header>
    <main id="conteudo">{children}</main>
  </div>;
}

export function Progress({ value }: { value: number }) {
  return <span className="progress" aria-label={`${value}% concluído`}>
    <span className="progress-track"><span className="progress-bar" style={{ width: `${value}%` }} /></span>
    <span className="progress-label">{value}%</span>
  </span>;
}

export function HealthBadge({ status, health }: { status: string; health: string }) {
  const badge = badgeFor(status, health);
  return <span className={`badge tone-${badge.tone}`}>{badge.label}</span>;
}

export function ProjectHeader({ project, crumbs }: { project: ProjectContext; crumbs: { label: string; href?: string }[] }) {
  return <header className="context">
    <nav className="crumbs" aria-label="Navegação">
      {crumbs.map((crumb, index) => <span key={`${crumb.label}-${index}`}>
        {index > 0 && <span aria-hidden="true"> / </span>}
        {crumb.href ? <AppLink href={crumb.href}>{crumb.label}</AppLink> : <span aria-current="page">{crumb.label}</span>}
      </span>)}
    </nav>
    <div className="context-title">
      <h1>{project.project_name}</h1>
      <HealthBadge status={project.project_status} health={project.project_health} />
    </div>
    <dl className="context-meta">
      <div><dt>Responsável</dt><dd>{project.project_owner.name}</dd></div>
      <div><dt>Prazo</dt><dd>{formatDate(project.project_due_date)}</dd></div>
      <div><dt>Status</dt><dd>{statusLabel(project.project_status)}</dd></div>
    </dl>
    <Progress value={project.project_progress} />
  </header>;
}

export function History({ events }: { events: ActivityEvent[] }) {
  if (!events.length) return <p className="muted">Nenhuma mudança registrada.</p>;
  return <ol className="history">
    {events.map(event => <li key={event.id}>
      <p>{event.actor_name} · {eventText(event)}</p>
      <time dateTime={event.created_at}>{formatWhen(event.created_at)}</time>
    </li>)}
  </ol>;
}
