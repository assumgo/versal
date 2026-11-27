import { useEffect, useState, type FormEvent } from 'react';
import { api, type ProjectList, type Template, type User } from '../api';
import { formatDate } from '../format';
import { STATUS_LABEL } from '../labels';
import { navigate, rememberPortfolio } from '../router';
import { AppLink, HealthBadge, Progress } from '../ui';

const PROJECT_STATUSES = ['rascunho', 'em_andamento', 'pausado', 'concluido', 'cancelado'] as const;

export function Portfolio({ user, search }: { user: User; search: string }) {
  const params = new URLSearchParams(search);
  const health = params.get('health');
  const status = params.get('status');
  const ownerId = params.get('owner_id');
  const [data, setData] = useState<ProjectList | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [savingProject, setSavingProject] = useState(false);
  const [addingPerson, setAddingPerson] = useState(false);
  const [savingPerson, setSavingPerson] = useState(false);
  const [query, setQuery] = useState(params.get('q') ?? '');
  const [templateKey, setTemplateKey] = useState('rack');

  function apply(next: URLSearchParams) {
    const search = next.toString();
    rememberPortfolio(search ? `?${search}` : '');
    navigate(search ? `/projects?${search}` : '/projects');
  }

  function toggleKpi(key: 'health' | 'status', value: string) {
    const next = new URLSearchParams(search);
    if (next.get(key) === value && (key === 'health' || !next.get('health'))) next.delete(key);
    else {
      next.set(key, value);
      if (key === 'health') next.delete('status');
      if (key === 'status') next.delete('health');
    }
    apply(next);
  }

  useEffect(() => {
    setQuery(new URLSearchParams(search).get('q') ?? '');
    rememberPortfolio(search);
    const current = new URLSearchParams(search);
    const path = `/api/projects?${new URLSearchParams({
      ...(current.get('q') ? { q: current.get('q')! } : {}),
      ...(current.get('owner_id') ? { owner_id: current.get('owner_id')! } : {}),
      ...(current.get('status') ? { status: current.get('status')! } : {}),
      ...(current.get('health') ? { health: current.get('health')! } : {}),
    })}`;
    let active = true;
    setLoading(true);
    Promise.all([
      api<ProjectList>(path),
      api<User[]>('/api/users'),
      api<Template[]>('/api/templates'),
    ]).then(([projects, people, models]) => {
      if (!active) return;
      setData(projects);
      setUsers(people);
      setTemplates(models);
      setError('');
    }).catch(cause => {
      if (active) setError(cause instanceof Error ? cause.message : 'Não foi possível carregar o portfólio.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [search]);

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSavingProject(true);
    setError('');
    try {
      const created = await api<{ project_id: number }>('/api/projects', {
        method: 'POST',
        body: JSON.stringify({
          name: String(form.get('name') ?? ''),
          owner_id: Number(form.get('owner_id')),
          due_date: String(form.get('due_date') || '') || null,
          template_key: String(form.get('template_key') || '') || null,
          status: form.get('draft') ? 'rascunho' : 'em_andamento',
        }),
      });
      navigate(`/projects/${created.project_id}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível criar o projeto.');
    } finally {
      setSavingProject(false);
    }
  }

  async function createPerson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSavingPerson(true);
    setError('');
    try {
      const created = await api<User>('/api/users', {
        method: 'POST',
        body: JSON.stringify({
          name: String(form.get('name') ?? ''),
          email: String(form.get('email') ?? ''),
          password: String(form.get('password') ?? ''),
        }),
      });
      setUsers(current => [...current, created].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')));
      event.currentTarget.reset();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível adicionar a pessoa.');
    } finally {
      setSavingPerson(false);
    }
  }

  const summary = data?.summary;
  const filtered = Boolean(query || health || status || ownerId);
  const selectedTemplate = templates.find(item => item.key === templateKey);

  return <section className="page">
    <div className="page-head">
      <div>
        <p className="eyebrow">Portfólio</p>
        <h1>Projetos</h1>
        <p className="lede">{data ? `Situação em ${formatDate(data.today)}, horário de São Paulo.` : 'Carregando a situação.'}</p>
      </div>
      <div className="head-actions">
        <button type="button" className="secondary" onClick={() => setAddingPerson(value => !value)}>Nova pessoa</button>
        <button type="button" onClick={() => setCreating(value => !value)}>Novo projeto</button>
      </div>
    </div>
    {error && <p className="alert" role="alert">{error}</p>}
    {addingPerson && <form className="panel" onSubmit={createPerson}>
      <h2>Nova pessoa</h2>
      <div className="fields">
        <label>Nome<input name="name" required maxLength={120} /></label>
        <label>E-mail<input name="email" type="email" required /></label>
        <label>Senha<input name="password" type="password" required minLength={8} autoComplete="new-password" /></label>
      </div>
      <button type="submit" disabled={savingPerson}>Adicionar</button>
    </form>}
    {creating && <form className="panel" onSubmit={createProject}>
      <h2>Novo projeto</h2>
      <div className="fields">
        <label>Nome<input name="name" required maxLength={200} /></label>
        <label>Responsável<select name="owner_id" defaultValue={String(user.id)}>{users.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}</select></label>
        <label>Prazo<input name="due_date" type="date" /></label>
        <label>Modelo<select name="template_key" value={templateKey} onChange={event => setTemplateKey(event.target.value)}>
          <option value="">Em branco</option>
          {templates.map(template => <option key={template.key} value={template.key}>{template.name}</option>)}
        </select></label>
      </div>
      {selectedTemplate && <p className="muted">Fases: {selectedTemplate.phases.map(phase => phase.name).join(', ')}.</p>}
      <label className="check"><input name="draft" type="checkbox" /> Criar como rascunho</label>
      <button type="submit" disabled={savingProject}>Criar projeto</button>
    </form>}
    <div className="kpis">
      <Kpi label="Ativos" value={summary?.ativos ?? 0} pressed={status === 'em_andamento' && !health} onClick={() => toggleKpi('status', 'em_andamento')} />
      <Kpi label="No prazo" value={summary?.no_prazo ?? 0} pressed={health === 'no_prazo'} onClick={() => toggleKpi('health', 'no_prazo')} />
      <Kpi label="Em atenção" value={summary?.atencao ?? 0} pressed={health === 'atencao'} onClick={() => toggleKpi('health', 'atencao')} />
      <Kpi label="Atrasados" value={summary?.atrasados ?? 0} pressed={health === 'atrasado'} onClick={() => toggleKpi('health', 'atrasado')} />
    </div>
    <form className="filters" onSubmit={event => {
      event.preventDefault();
      const next = new URLSearchParams(search);
      if (query.trim()) next.set('q', query.trim());
      else next.delete('q');
      apply(next);
    }}>
      <label>Buscar<input value={query} onChange={event => setQuery(event.target.value)} /></label>
      <label>Responsável<select value={ownerId ?? ''} onChange={event => {
        const next = new URLSearchParams(search);
        if (event.target.value) next.set('owner_id', event.target.value);
        else next.delete('owner_id');
        apply(next);
      }}><option value="">Todos</option>{users.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}</select></label>
      <label>Status<select value={status ?? ''} onChange={event => {
        const next = new URLSearchParams(search);
        if (event.target.value) next.set('status', event.target.value);
        else next.delete('status');
        apply(next);
      }}><option value="">Todos</option>{PROJECT_STATUSES.map(item => <option key={item} value={item}>{STATUS_LABEL[item]}</option>)}</select></label>
      <button type="submit" className="secondary">Buscar</button>
    </form>
    {loading && <p className="muted">Carregando projetos…</p>}
    {!loading && data && data.projects.length === 0 && <p className="empty">{filtered ? 'Nenhum projeto com esse filtro.' : 'Nenhum projeto ainda. Crie o primeiro para acompanhar da abertura à entrega.'}</p>}
    {data && data.projects.length > 0 && <ul className="project-list">
      {data.projects.map(project => <li key={project.id}>
        <AppLink className="project-row" href={`/projects/${project.id}`}>
          <HealthBadge status={project.status} health={project.health} />
          <span><strong>{project.name}</strong><small>{project.owner.name}</small></span>
          <span>{formatDate(project.due_date)}</span>
          <Progress value={project.progress} />
          <span>{project.next_overdue_on ? `Venceu ${formatDate(project.next_overdue_on)}` : 'Sem atraso'}</span>
        </AppLink>
      </li>)}
    </ul>}
  </section>;
}

function Kpi({ label, value, pressed, onClick }: { label: string; value: number; pressed: boolean; onClick: () => void }) {
  return <button type="button" className={`kpi${pressed ? ' selected' : ''}`} aria-pressed={pressed} onClick={onClick}>
    <span className="kpi-value">{value}</span>
    <span className="kpi-label">{label}</span>
  </button>;
}
