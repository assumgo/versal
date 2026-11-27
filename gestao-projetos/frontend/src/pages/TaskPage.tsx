import { useEffect, useState, type FormEvent } from 'react';
import { api, type TaskDetail, type User } from '../api';
import { portfolioHref } from '../router';
import { History, ProjectHeader } from '../ui';

export function TaskPage({ projectId, phaseId, taskId }: { projectId: number; phaseId: number; taskId: number }) {
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [status, setStatus] = useState('a_fazer');

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([api<TaskDetail>(`/api/tasks/${taskId}`), api<User[]>('/api/users')]).then(([detail, people]) => {
      if (!active) return;
      setTask(detail);
      setStatus(detail.status);
      setUsers(people);
      setError('');
    }).catch(cause => {
      if (active) setError(cause instanceof Error ? cause.message : 'Não foi possível abrir a tarefa.');
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [taskId]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError('');
    try {
      const updated = await api<TaskDetail>(`/api/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify({
          title: String(form.get('title') ?? ''),
          description: String(form.get('description') ?? ''),
          status: String(form.get('status') ?? 'a_fazer'),
          assignee_id: String(form.get('assignee_id') || '') ? Number(form.get('assignee_id')) : null,
          due_date: String(form.get('due_date') || '') || null,
          blocked_reason: String(form.get('blocked_reason') || '') || null,
        }),
      });
      setTask(updated);
      setStatus(updated.status);
      setNotice(`Salvo. Projeto em ${updated.project_progress}%. Fase ${updated.phase_name} em ${updated.phase_progress}% (${updated.phase_done_tasks} de ${updated.phase_total_tasks}).`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível salvar a tarefa.');
    } finally {
      setPending(false);
    }
  }

  if (loading && !task) return <p className="muted">Carregando tarefa…</p>;
  if (!task) return <p className="alert" role="alert">{error || 'Tarefa não encontrada.'}</p>;

  return <section className="page">
    <ProjectHeader project={task} crumbs={[
      { label: 'Projetos', href: portfolioHref() },
      { label: task.project_name, href: `/projects/${projectId}` },
      { label: task.phase_name, href: `/projects/${projectId}/phases/${phaseId}` },
      { label: task.title },
    ]} />
    {error && <p className="alert" role="alert">{error}</p>}
    {notice && <p className="notice" role="status">{notice}</p>}
    {task.overdue && <p className="alert">Esta tarefa está atrasada.</p>}
    <form className="panel" onSubmit={save}>
      <div className="fields">
        <label className="wide">Título<input name="title" defaultValue={task.title} required maxLength={200} /></label>
        <label>Status<select name="status" value={status} onChange={event => setStatus(event.target.value)}>
          <option value="a_fazer">A fazer</option>
          <option value="em_andamento">Em andamento</option>
          <option value="bloqueada">Bloqueada</option>
          <option value="concluida">Concluída</option>
        </select></label>
        <label>Responsável<select name="assignee_id" defaultValue={task.assignee?.id ?? ''}>
          <option value="">Sem responsável</option>
          {users.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}
        </select></label>
        <label>Prazo<input name="due_date" type="date" defaultValue={task.due_date ?? ''} /></label>
        {status === 'bloqueada' && <label className="wide">Motivo do bloqueio<input name="blocked_reason" defaultValue={task.blocked_reason ?? ''} required maxLength={280} /></label>}
        <label className="wide">Descrição<textarea name="description" defaultValue={task.description} rows={4} maxLength={4000} /></label>
      </div>
      <button type="submit" disabled={pending}>{pending ? 'Salvando…' : 'Salvar tarefa'}</button>
    </form>
    <section>
      <h2>Histórico</h2>
      <History events={task.events} />
    </section>
  </section>;
}
