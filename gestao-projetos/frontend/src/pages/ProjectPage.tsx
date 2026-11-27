import { useEffect, useState, type FormEvent } from 'react';
import { api, openTaskCount, type ProjectDetail, type TaskItem, type User } from '../api';
import { formatDate } from '../format';
import { statusLabel } from '../labels';
import { navigate, portfolioHref } from '../router';
import { AppLink, History, ProjectHeader, Progress } from '../ui';

const ACTIONS: Record<string, { status: string; label: string }[]> = {
  rascunho: [
    { status: 'em_andamento', label: 'Iniciar' },
    { status: 'cancelado', label: 'Cancelar' },
  ],
  em_andamento: [
    { status: 'pausado', label: 'Pausar' },
    { status: 'concluido', label: 'Concluir' },
    { status: 'cancelado', label: 'Cancelar' },
  ],
  pausado: [
    { status: 'em_andamento', label: 'Retomar' },
    { status: 'concluido', label: 'Concluir' },
    { status: 'cancelado', label: 'Cancelar' },
  ],
  concluido: [{ status: 'em_andamento', label: 'Reabrir' }],
  cancelado: [{ status: 'em_andamento', label: 'Reabrir' }],
};

const FILTER_LABEL: Record<string, string> = {
  todas: 'todas as tarefas',
  abertas: 'tarefas abertas',
  concluidas: 'tarefas concluídas',
  atrasadas: 'tarefas atrasadas',
  bloqueadas: 'tarefas bloqueadas',
};

const EMPTY_FILTER: Record<string, string> = {
  todas: 'Este projeto ainda não tem tarefas.',
  abertas: 'Nenhuma tarefa aberta.',
  concluidas: 'Nenhuma tarefa concluída.',
  atrasadas: 'Nenhuma tarefa atrasada.',
  bloqueadas: 'Nenhuma tarefa bloqueada.',
};

export function ProjectPage({ projectId, filtro }: { projectId: number; filtro: string | null }) {
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [confirmCount, setConfirmCount] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    const requests: [Promise<ProjectDetail>, Promise<User[]>, Promise<TaskItem[]> | null] = [
      api<ProjectDetail>(`/api/projects/${projectId}`),
      api<User[]>('/api/users'),
      filtro ? api<TaskItem[]>(`/api/projects/${projectId}/tasks?filtro=${encodeURIComponent(filtro)}`) : null,
    ];
    Promise.all(requests.filter(Boolean) as Promise<unknown>[]).then(results => {
      if (!active) return;
      setProject(results[0] as ProjectDetail);
      setUsers(results[1] as User[]);
      setTasks(filtro ? results[2] as TaskItem[] : []);
      setError('');
    }).catch(cause => {
      if (active) setError(cause instanceof Error ? cause.message : 'Não foi possível abrir o projeto.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [projectId, filtro]);

  async function changeStatus(status: string, confirm = false) {
    setPending(true);
    setError('');
    try {
      const updated = await api<ProjectDetail>(`/api/projects/${projectId}/status`, {
        method: 'POST',
        body: JSON.stringify({ status, confirm_open_tasks: confirm }),
      });
      setProject(updated);
      setConfirmCount(null);
      setNotice(`Status atualizado para ${statusLabel(updated.project_status)}.`);
    } catch (cause) {
      const count = openTaskCount(cause);
      if (count !== null) setConfirmCount(count);
      else setError(cause instanceof Error ? cause.message : 'Não foi possível mudar o status.');
    } finally {
      setPending(false);
    }
  }

  async function saveProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError('');
    try {
      const updated = await api<ProjectDetail>(`/api/projects/${projectId}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: String(form.get('name') ?? ''),
          description: String(form.get('description') ?? ''),
          owner_id: Number(form.get('owner_id')),
          start_date: String(form.get('start_date') || '') || null,
          due_date: String(form.get('due_date') || '') || null,
        }),
      });
      setProject(updated);
      setNotice('Dados do projeto atualizados.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível salvar o projeto.');
    } finally {
      setPending(false);
    }
  }

  async function addPhase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setPending(true);
    setError('');
    try {
      await api(`/api/projects/${projectId}/phases`, {
        method: 'POST',
        body: JSON.stringify({
          name: String(data.get('name') ?? ''),
          due_date: String(data.get('due_date') || '') || null,
        }),
      });
      form.reset();
      const updated = await api<ProjectDetail>(`/api/projects/${projectId}`);
      setProject(updated);
      setNotice('Fase adicionada.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível adicionar a fase.');
    } finally {
      setPending(false);
    }
  }

  async function movePhase(index: number, direction: -1 | 1) {
    if (!project) return;
    const ids = project.phases.map(phase => phase.id);
    const target = index + direction;
    if (target < 0 || target >= ids.length) return;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    setPending(true);
    try {
      setProject(await api<ProjectDetail>(`/api/projects/${projectId}/phases/reorder`, {
        method: 'POST',
        body: JSON.stringify({ ids }),
      }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível reordenar as fases.');
    } finally {
      setPending(false);
    }
  }

  async function removeDraft() {
    setPending(true);
    try {
      await api(`/api/projects/${projectId}`, { method: 'DELETE' });
      navigate(portfolioHref());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível apagar o rascunho.');
      setPending(false);
    }
  }

  function openFilter(next: string) {
    navigate(filtro === next ? `/projects/${projectId}` : `/projects/${projectId}?filtro=${next}`);
  }

  if (loading && !project) return <p className="muted">Carregando projeto…</p>;
  if (!project) return <p className="alert" role="alert">{error || 'Projeto não encontrado.'}</p>;

  const crumbs = [
    { label: 'Projetos', href: portfolioHref() },
    { label: project.project_name },
  ];

  return <section className="page">
    <ProjectHeader project={project} crumbs={crumbs} />
    {error && <p className="alert" role="alert">{error}</p>}
    {notice && <p className="notice" role="status">{notice}</p>}
    <div className="kpis">
      <FilterKpi label="Tarefas" value={project.total_tasks} filtro="todas" current={filtro} onClick={openFilter} />
      <FilterKpi label="Concluídas" value={project.done_tasks} filtro="concluidas" current={filtro} onClick={openFilter} />
      <FilterKpi label="Atrasadas" value={project.overdue_tasks} filtro="atrasadas" current={filtro} onClick={openFilter} />
      <FilterKpi label="Bloqueadas" value={project.blocked_tasks} filtro="bloqueadas" current={filtro} onClick={openFilter} />
    </div>
    <div className="actions">
      {(ACTIONS[project.project_status] ?? []).map(action => <button key={action.status} type="button" className={action.status === 'concluido' ? '' : 'secondary'} disabled={pending} onClick={() => { void changeStatus(action.status); }}>{action.label}</button>)}
      {project.project_status === 'rascunho' && <button type="button" className="danger" disabled={pending} onClick={() => { void removeDraft(); }}>Apagar rascunho</button>}
    </div>
    {confirmCount !== null && <div className="panel confirm" role="alertdialog" aria-labelledby="confirm-title">
      <h2 id="confirm-title">Concluir com tarefas abertas?</h2>
      <p>Ainda há {confirmCount} {confirmCount === 1 ? 'tarefa aberta' : 'tarefas abertas'}. O projeto pode ser concluído mesmo assim.</p>
      <div className="actions">
        <button type="button" disabled={pending} onClick={() => { void changeStatus('concluido', true); }}>Concluir mesmo assim</button>
        <button type="button" className="secondary" onClick={() => setConfirmCount(null)}>Voltar</button>
      </div>
    </div>}
    {filtro && <section>
      <div className="section-head">
        <h2>Mostrando {FILTER_LABEL[filtro] ?? 'tarefas'}</h2>
        <button type="button" className="secondary" onClick={() => navigate(`/projects/${projectId}`)}>Ver fases</button>
      </div>
      {tasks.length === 0 && <p className="empty">{EMPTY_FILTER[filtro] ?? 'Nenhuma tarefa encontrada.'}</p>}
      <ul className="task-list">
        {tasks.map(task => <li key={task.id}>
          <AppLink href={`/projects/${project.project_id}/phases/${task.phase_id}/tasks/${task.id}`}>
            <strong>{task.title}</strong>
            <small>{task.phase_name} · {statusLabel(task.status)} · {task.assignee?.name ?? 'Sem responsável'} · {formatDate(task.due_date)}</small>
            {task.blocked_reason && <small>Motivo: {task.blocked_reason}</small>}
          </AppLink>
        </li>)}
      </ul>
    </section>}
    {!filtro && <>
      {project.schedule_conflicts.length > 0 && <section className="panel warning">
        <h2>Prazo além do projeto</h2>
        <ul className="task-list">
          {project.schedule_conflicts.map(conflict => <li key={conflict.id}>
            <AppLink href={`/projects/${project.project_id}/phases/${conflict.phase_id}/tasks/${conflict.id}`}>
              <strong>{conflict.title}</strong>
              <small>{conflict.phase_name} · vence em {formatDate(conflict.due_date)}, depois do prazo do projeto</small>
            </AppLink>
          </li>)}
        </ul>
      </section>}
      <section>
        <h2>Fases</h2>
        {project.phases.length === 0 && <p className="empty">Nenhuma fase ainda. Adicione a primeira para organizar o trabalho.</p>}
        <ol className="phase-list">
          {project.phases.map((phase, index) => <li key={phase.id} className="phase-row">
            <AppLink className="phase-main" href={`/projects/${project.project_id}/phases/${phase.id}`}>
              <strong>{phase.name}</strong>
              <small>{statusLabel(phase.status)} · prazo {formatDate(phase.due_date)}</small>
              <Progress value={phase.progress} />
            </AppLink>
            <AppLink className={phase.overdue_tasks ? 'late-link' : 'quiet-link'} href={`/projects/${project.project_id}/phases/${phase.id}?filtro=atrasadas`}>{phase.overdue_tasks} atrasadas</AppLink>
            <div className="reorder">
              <button type="button" disabled={pending || index === 0} onClick={() => { void movePhase(index, -1); }}>Subir</button>
              <button type="button" disabled={pending || index === project.phases.length - 1} onClick={() => { void movePhase(index, 1); }}>Descer</button>
            </div>
          </li>)}
        </ol>
        <form className="inline-form" onSubmit={addPhase}>
          <label>Nova fase<input name="name" required maxLength={120} /></label>
          <label>Prazo<input name="due_date" type="date" /></label>
          <button type="submit" disabled={pending}>Adicionar fase</button>
        </form>
      </section>
      <details className="panel">
        <summary>Dados do projeto</summary>
        <form onSubmit={saveProject}>
          <div className="fields">
            <label>Nome<input name="name" defaultValue={project.project_name} required maxLength={200} /></label>
            <label>Responsável<select name="owner_id" defaultValue={project.project_owner.id}>{users.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}</select></label>
            <label>Início<input name="start_date" type="date" defaultValue={project.start_date ?? ''} /></label>
            <label>Prazo<input name="due_date" type="date" defaultValue={project.project_due_date ?? ''} /></label>
            <label className="wide">Descrição<textarea name="description" defaultValue={project.description} maxLength={4000} rows={3} /></label>
          </div>
          <button type="submit" disabled={pending}>Salvar dados</button>
        </form>
      </details>
      <section>
        <h2>Histórico</h2>
        <History events={project.events} />
      </section>
    </>}
  </section>;
}

function FilterKpi({ label, value, filtro, current, onClick }: { label: string; value: number; filtro: string; current: string | null; onClick: (filtro: string) => void }) {
  return <button type="button" className={`kpi${current === filtro ? ' selected' : ''}`} aria-pressed={current === filtro} onClick={() => onClick(filtro)}>
    <span className="kpi-value">{value}</span>
    <span className="kpi-label">{label}</span>
  </button>;
}
