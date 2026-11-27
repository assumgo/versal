from datetime import date

CLOSED_PROJECT_STATUSES = frozenset({'pausado', 'concluido', 'cancelado'})
OPEN_PROJECT_STATUSES = frozenset({'rascunho', 'em_andamento'})
STATUS_TRANSITIONS = {
    'rascunho': frozenset({'em_andamento', 'cancelado'}),
    'em_andamento': frozenset({'pausado', 'concluido', 'cancelado'}),
    'pausado': frozenset({'em_andamento', 'concluido', 'cancelado'}),
    'concluido': frozenset({'em_andamento'}),
    'cancelado': frozenset({'em_andamento'}),
}


def progress_percent(done: int, total: int, *, empty_is_complete: bool = False) -> int:
    """Percent from task counts. Stays below 100 while any task is still open."""
    if total <= 0:
        return 100 if empty_is_complete else 0
    if done >= total:
        return 100
    return (100 * done) // total


def project_health(
    *,
    status: str,
    due_date: date | None,
    overdue_tasks: int,
    blocked_tasks: int,
    phase_attention: bool,
    today: date,
) -> str:
    if status in CLOSED_PROJECT_STATUSES:
        return status
    if (due_date is not None and due_date < today) or overdue_tasks > 0:
        return 'atrasado'
    if blocked_tasks > 0 or phase_attention:
        return 'atencao'
    return 'no_prazo'


def task_is_overdue(due_date: date | None, status: str, today: date) -> bool:
    return due_date is not None and due_date < today and status != 'concluida'


def next_overdue_on(
    *,
    status: str,
    due_date: date | None,
    earliest_task_due: date | None,
    today: date,
    health: str,
) -> date | None:
    if health != 'atrasado':
        return None
    candidates: list[date] = []
    if earliest_task_due is not None:
        candidates.append(earliest_task_due)
    if status in OPEN_PROJECT_STATUSES and due_date is not None and due_date < today:
        candidates.append(due_date)
    return min(candidates) if candidates else None
