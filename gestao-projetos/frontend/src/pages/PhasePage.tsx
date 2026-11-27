import { useEffect, useState, type FormEvent } from 'react';
import { api, type PhaseDetail } from '../api';
import { formatDate } from '../format';
import { statusLabel } from '../labels';
import { portfolioHref } from '../router';
import { AppLink, ProjectHeader, Progress } from '../ui';

export function PhasePage({ projectId, phaseId, filtro }: { projectId: number; phaseId: number; filtro: string | null }) {
  const [phase, setPhase] = useState<PhaseDetail | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);

  function load() {
    setLoading(true);
    return api<PhaseDetail>(`/api/phases/${phaseId}`).then(result => {
      setPhase(result);
      setError('');
    }).catch(cause => {
      setError(cause instanceof Error ? cause.message : 'Não foi possível abrir a fase.');
    }).finally(() => setLoading(false));
  }

  useEffect(() => { void load(); }, [phaseId]);

  async function savePhase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError('');
    try {
      setPhase(await api<PhaseDetail>(`/api/phases/${phaseId}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: String(form.get('name') ?? ''),
          status: String(form.get('status') ?? 'nao_iniciada'),
          start_date: String(form.get('start_date') || '') || null,
          due_date: String(form.get('due_date') || '') || null,
        }),
      }));
      setNotice('Fase atualizada.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível salvar a fase.');
    } finally {
      setPending(false);
    }
  }

  async function addTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setPending(true);
    setError('');
    try {
      await api(`/api/phases/${phaseId}/tasks`, {
        method: 'POST',
        body: JSON.stringify({ title: String(data.get('title') ?? '') }),
      });
      form.reset();
      await load();
      setNotice('Tarefa adicionada.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível adicionar a tarefa.');
    } finally {
      setPending(false);
    }
  }

  async function moveTask(index: number, direction: -1 | 1) {
    if (!phase) return;
    const ids = phase.tasks.map(task => task.id);
    const target = index + direction;
    if (target < 0 || target >= ids.length) return;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    setPending(true);
    try {
      setPhase(await api<PhaseDetail>(`/api/phases/${phaseId}/tasks/reorder`, {
        method: 'POST',
        body: JSON.stringify({ ids }),
      }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível reordenar as tarefas.');
    } finally {
      setPending(false);
    }
  }

  if (loading && !phase) return <p className="muted">Carregando fase…</p>;
  if (!phase) return <p className="alert" role="alert">{error || 'Fase não encontrada.'}</p>;

  const visible = phase.tasks.filter(task => {
    if (filtro === 'atrasadas') return task.overdue;
    if (filtro === 'bloqueadas') return task.status === 'bloqueada';
    if (filtro === 'concluidas') return task.status === 'concluida';
    if (filtro === 'abertas') return task.status !== 'concluida';
    return true;
  });

  return <section className="page">
    <ProjectHeader project={phase} crumbs={[
      { label: 'Projetos', href: portfolioHref() },
      { label: phase.project_name, href: `/projects/${projectId}` },
      { label: phase.name },
    ]} />
    {error && <p className="alert" role="alert">{error}</p>}
    {notice && <p className="notice" role="status">{notice}</p>}
    <p className="phase-summary">{statusLabel(phase.status)} · {phase.done_tasks} de {phase.total_tasks} tarefas · <Progress value={phase.progress} /></p>
    {filtro === 'atrasadas' && <p className="muted">Mostrando tarefas atrasadas desta fase. <AppLink href={`/projects/${projectId}/phases/${phaseId}`}>Ver todas</AppLink></p>}
    {visible.length === 0 && <p className="empty">{filtro === 'atrasadas' ? 'Nenhuma tarefa atrasada nesta fase.' : 'Nenhuma tarefa nesta fase. Adicione a primeira abaixo.'}</p>}
    <ul className="task-list">
      {visible.map(task => {
        const index = phase.tasks.findIndex(item => item.id === task.id);
        return <li key={task.id} className="task-row">
          <AppLink href={`/projects/${projectId}/phases/${phaseId}/tasks/${task.id}`}>
            <strong>{task.title}</strong>
            <small>{statusLabel(task.status)}{task.overdue ? ' · Atrasada' : ''} · {task.assignee?.name ?? 'Sem responsável'} · {formatDate(task.due_date)}</small>
            {task.blocked_reason && <small>Motivo: {task.blocked_reason}</small>}
          </AppLink>
          <div className="reorder">
            <button type="button" disabled={pending || index === 0} onClick={() => { void moveTask(index, -1); }}>Subir</button>
            <button type="button" disabled={pending || index === phase.tasks.length - 1} onClick={() => { void moveTask(index, 1); }}>Descer</button>
          </div>
        </li>;
      })}
    </ul>
    <form className="inline-form" onSubmit={addTask}>
      <label>Nova tarefa<input name="title" required maxLength={200} /></label>
      <button type="submit" disabled={pending}>Adicionar tarefa</button>
    </form>
    <form className="panel" onSubmit={savePhase}>
      <h2>Dados da fase</h2>
      <div className="fields">
        <label>Nome<input name="name" defaultValue={phase.name} required maxLength={120} /></label>
        <label>Status<select name="status" defaultValue={phase.status}>
          <option value="nao_iniciada">Não iniciada</option>
          <option value="em_andamento">Em andamento</option>
          <option value="concluida">Concluída</option>
        </select></label>
        <label>Início<input name="start_date" type="date" defaultValue={phase.start_date ?? ''} /></label>
        <label>Prazo<input name="due_date" type="date" defaultValue={phase.due_date ?? ''} /></label>
      </div>
      <button type="submit" disabled={pending}>Salvar fase</button>
    </form>
  </section>;
}
