from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.time import now_utc, today as clock_today
from app.models.entities import ActivityEvent, Phase, Project, Task, User
from app.schemas.projects import (
    ActivityEventOut,
    PhaseCreate,
    PhaseDetail,
    PhaseListItem,
    PhaseUpdate,
    ProjectCreate,
    ProjectDetail,
    ProjectListItem,
    ProjectListResponse,
    ProjectSummary,
    ProjectUpdate,
    StatusChange,
    TaskConflict,
    TaskCreate,
    TaskDetail,
    TaskListItem,
    TaskUpdate,
    UserOut,
)
from app.services.catalog import get_template
from app.services.health import (
    STATUS_TRANSITIONS,
    next_overdue_on,
    progress_percent,
    project_health,
    task_is_overdue,
)


def _missing(label: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f'{label} não encontrado.')


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, name=user.name, email=user.email)


def _as_date(value: date | str | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _as_int(value: object) -> int:
    return int(value or 0)


def _require_user(session: Session, user_id: int, label: str) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=422, detail=f'{label} não encontrado.')
    return user


def _record(
    session: Session,
    *,
    project_id: int,
    actor_id: int,
    event_type: str,
    old_value: str | None = None,
    new_value: str | None = None,
    task_id: int | None = None,
) -> None:
    session.add(ActivityEvent(
        project_id=project_id,
        task_id=task_id,
        actor_id=actor_id,
        event_type=event_type,
        old_value=old_value,
        new_value=new_value,
        created_at=now_utc(),
    ))


def _touch(project: Project) -> None:
    project.updated_at = now_utc()


def _overdue_condition(day: date):
    return and_(Task.due_date.is_not(None), Task.due_date < day, Task.status != 'concluida')


def _project_aggregates(day: date):
    overdue = _overdue_condition(day)
    return (
        select(
            Phase.project_id.label('project_id'),
            func.count(Task.id).label('total_tasks'),
            func.coalesce(func.sum(case((Task.status == 'concluida', 1), else_=0)), 0).label('done_tasks'),
            func.coalesce(func.sum(case((overdue, 1), else_=0)), 0).label('overdue_tasks'),
            func.coalesce(func.sum(case((Task.status == 'bloqueada', 1), else_=0)), 0).label('blocked_tasks'),
            func.min(case((overdue, Task.due_date), else_=None)).label('next_overdue_on'),
        )
        .select_from(Phase)
        .outerjoin(Task, Task.phase_id == Phase.id)
        .group_by(Phase.project_id)
    ).subquery()


def _phase_attention(day: date):
    horizon = day + timedelta(days=7)
    open_task = (
        select(Task.id)
        .where(Task.phase_id == Phase.id, Task.status != 'concluida')
        .exists()
    )
    return (
        select(Phase.id)
        .where(
            Phase.project_id == Project.id,
            Phase.due_date.is_not(None),
            Phase.due_date >= day,
            Phase.due_date <= horizon,
            open_task,
        )
        .exists()
    )


def _load_project(session: Session, project_id: int) -> Project:
    project = session.scalar(
        select(Project).options(selectinload(Project.owner)).where(Project.id == project_id)
    )
    if project is None:
        raise _missing('Projeto')
    return project


def _metrics(session: Session, project: Project, day: date) -> dict:
    aggregates = _project_aggregates(day)
    row = session.execute(
        select(
            func.coalesce(aggregates.c.total_tasks, 0),
            func.coalesce(aggregates.c.done_tasks, 0),
            func.coalesce(aggregates.c.overdue_tasks, 0),
            func.coalesce(aggregates.c.blocked_tasks, 0),
            aggregates.c.next_overdue_on,
            _phase_attention(day),
        ).select_from(Project).outerjoin(aggregates, aggregates.c.project_id == Project.id)
        .where(Project.id == project.id)
    ).one()
    total, done, overdue, blocked, earliest, attention = row
    total_i, done_i, overdue_i, blocked_i = _as_int(total), _as_int(done), _as_int(overdue), _as_int(blocked)
    health = project_health(
        status=project.status,
        due_date=project.due_date,
        overdue_tasks=overdue_i,
        blocked_tasks=blocked_i,
        phase_attention=bool(attention),
        today=day,
    )
    return {
        'total': total_i,
        'done': done_i,
        'overdue': overdue_i,
        'blocked': blocked_i,
        'health': health,
        'progress': progress_percent(done_i, total_i),
        'next_overdue_on': next_overdue_on(
            status=project.status,
            due_date=project.due_date,
            earliest_task_due=_as_date(earliest),
            today=day,
            health=health,
        ),
    }


def _events(session: Session, project_id: int, task_id: int | None) -> list[ActivityEventOut]:
    statement = (
        select(ActivityEvent, User.name)
        .join(User, User.id == ActivityEvent.actor_id)
        .where(ActivityEvent.project_id == project_id)
        .order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc())
    )
    if task_id is None:
        statement = statement.where(ActivityEvent.task_id.is_(None))
    else:
        statement = statement.where(ActivityEvent.task_id == task_id)
    return [
        ActivityEventOut(
            id=event.id,
            event_type=event.event_type,
            old_value=event.old_value,
            new_value=event.new_value,
            actor_name=actor_name,
            created_at=event.created_at,
            task_id=event.task_id,
        )
        for event, actor_name in session.execute(statement)
    ]


def _context(project: Project, metrics: dict) -> dict:
    return {
        'project_id': project.id,
        'project_name': project.name,
        'project_status': project.status,
        'project_health': metrics['health'],
        'project_progress': metrics['progress'],
        'project_due_date': project.due_date,
        'project_owner': _user_out(project.owner),
    }


def _phase_rows(session: Session, project_id: int, day: date) -> list[PhaseListItem]:
    overdue = _overdue_condition(day)
    task_counts = (
        select(
            Task.phase_id.label('phase_id'),
            func.count(Task.id).label('total_tasks'),
            func.coalesce(func.sum(case((Task.status == 'concluida', 1), else_=0)), 0).label('done_tasks'),
            func.coalesce(func.sum(case((overdue, 1), else_=0)), 0).label('overdue_tasks'),
        )
        .group_by(Task.phase_id)
    ).subquery()
    rows = session.execute(
        select(
            Phase,
            func.coalesce(task_counts.c.total_tasks, 0),
            func.coalesce(task_counts.c.done_tasks, 0),
            func.coalesce(task_counts.c.overdue_tasks, 0),
        )
        .outerjoin(task_counts, task_counts.c.phase_id == Phase.id)
        .where(Phase.project_id == project_id)
        .order_by(Phase.position, Phase.id)
    )
    items = []
    for phase, total, done, late in rows:
        total_i, done_i, late_i = _as_int(total), _as_int(done), _as_int(late)
        items.append(PhaseListItem(
            id=phase.id,
            name=phase.name,
            status=phase.status,
            position=phase.position,
            start_date=phase.start_date,
            due_date=phase.due_date,
            progress=progress_percent(done_i, total_i, empty_is_complete=phase.status == 'concluida'),
            total_tasks=total_i,
            done_tasks=done_i,
            overdue_tasks=late_i,
        ))
    return items


def _task_item(task: Task, phase: Phase, day: date) -> TaskListItem:
    return TaskListItem(
        id=task.id,
        phase_id=phase.id,
        phase_name=phase.name,
        title=task.title,
        status=task.status,
        assignee=_user_out(task.assignee) if task.assignee is not None else None,
        due_date=task.due_date,
        overdue=task_is_overdue(task.due_date, task.status, day),
        blocked_reason=task.blocked_reason,
        position=task.position,
    )


def _conflicts(session: Session, project: Project) -> list[TaskConflict]:
    if project.due_date is None:
        return []
    rows = session.execute(
        select(Task, Phase)
        .join(Phase, Phase.id == Task.phase_id)
        .where(
            Phase.project_id == project.id,
            Task.due_date.is_not(None),
            Task.due_date > project.due_date,
        )
        .order_by(Phase.position, Task.position)
    )
    return [
        TaskConflict(id=task.id, title=task.title, phase_id=phase.id, phase_name=phase.name, due_date=task.due_date)
        for task, phase in rows
        if task.due_date is not None
    ]


def _reorder(session: Session, rows: list, ordered_ids: list[int]) -> None:
    by_id = {row.id: row for row in rows}
    if len(ordered_ids) != len(by_id) or set(ordered_ids) != set(by_id):
        raise HTTPException(status_code=422, detail='A ordem precisa incluir cada item uma vez.')
    for index, item_id in enumerate(ordered_ids):
        by_id[item_id].position = -(index + 1)
    session.flush()
    for index, item_id in enumerate(ordered_ids):
        by_id[item_id].position = index


def _copy_template(session: Session, project: Project, template_key: str) -> None:
    template = get_template(session, template_key)
    if template is None:
        raise HTTPException(status_code=422, detail='Modelo não encontrado.')
    for phase_template in sorted(template.phases, key=lambda item: item.position):
        phase = Phase(
            project_id=project.id,
            name=phase_template.name,
            position=phase_template.position,
            status='nao_iniciada',
        )
        session.add(phase)
        session.flush()
        for task_template in sorted(phase_template.tasks, key=lambda item: item.position):
            session.add(Task(
                phase_id=phase.id,
                title=task_template.title,
                description='',
                position=task_template.position,
                status='a_fazer',
            ))


def list_projects(
    session: Session,
    *,
    query: str | None,
    owner_id: int | None,
    status: str | None,
    health: str | None,
    day: date | None = None,
) -> ProjectListResponse:
    day = day or clock_today()
    aggregates = _project_aggregates(day)
    rows = session.execute(
        select(
            Project,
            User,
            func.coalesce(aggregates.c.total_tasks, 0),
            func.coalesce(aggregates.c.done_tasks, 0),
            func.coalesce(aggregates.c.overdue_tasks, 0),
            func.coalesce(aggregates.c.blocked_tasks, 0),
            aggregates.c.next_overdue_on,
            _phase_attention(day),
        )
        .join(User, User.id == Project.owner_id)
        .outerjoin(aggregates, aggregates.c.project_id == Project.id)
    ).all()
    items: list[ProjectListItem] = []
    summary = {'ativos': 0, 'no_prazo': 0, 'atencao': 0, 'atrasados': 0}
    folded_query = query.strip().casefold() if query else ''
    for project, owner, total, done, overdue, blocked, earliest, attention in rows:
        total_i, done_i = _as_int(total), _as_int(done)
        overdue_i, blocked_i = _as_int(overdue), _as_int(blocked)
        item_health = project_health(
            status=project.status,
            due_date=project.due_date,
            overdue_tasks=overdue_i,
            blocked_tasks=blocked_i,
            phase_attention=bool(attention),
            today=day,
        )
        if project.status == 'em_andamento':
            summary['ativos'] += 1
        if item_health == 'no_prazo':
            summary['no_prazo'] += 1
        elif item_health == 'atencao':
            summary['atencao'] += 1
        elif item_health == 'atrasado':
            summary['atrasados'] += 1
        if folded_query and folded_query not in project.name.casefold():
            continue
        if owner_id is not None and project.owner_id != owner_id:
            continue
        if status is not None and project.status != status:
            continue
        if health is not None and item_health != health:
            continue
        items.append(ProjectListItem(
            id=project.id,
            name=project.name,
            status=project.status,
            health=item_health,
            owner=_user_out(owner),
            due_date=project.due_date,
            progress=progress_percent(done_i, total_i),
            next_overdue_on=next_overdue_on(
                status=project.status,
                due_date=project.due_date,
                earliest_task_due=_as_date(earliest),
                today=day,
                health=item_health,
            ),
            total_tasks=total_i,
            done_tasks=done_i,
        ))
    rank = {'atrasado': 0, 'atencao': 1, 'no_prazo': 2, 'pausado': 3, 'concluido': 4, 'cancelado': 5}
    items.sort(key=lambda item: (rank.get(item.health, 9), item.due_date or date.max, item.name.casefold()))
    return ProjectListResponse(today=day, summary=ProjectSummary(**summary), projects=items)


def create_project(session: Session, payload: ProjectCreate, actor: User) -> ProjectDetail:
    owner = _require_user(session, payload.owner_id, 'Responsável')
    moment = now_utc()
    project = Project(
        name=payload.name,
        description=payload.description,
        status=payload.status,
        start_date=payload.start_date,
        due_date=payload.due_date,
        owner_id=owner.id,
        created_at=moment,
        updated_at=moment,
    )
    session.add(project)
    session.flush()
    if payload.template_key:
        _copy_template(session, project, payload.template_key)
    _record(
        session,
        project_id=project.id,
        actor_id=actor.id,
        event_type='project_created',
        new_value=project.name,
    )
    session.flush()
    return get_project(session, project.id)


def get_project(session: Session, project_id: int, day: date | None = None) -> ProjectDetail:
    day = day or clock_today()
    project = _load_project(session, project_id)
    metrics = _metrics(session, project, day)
    return ProjectDetail(
        **_context(project, metrics),
        description=project.description,
        start_date=project.start_date,
        total_tasks=metrics['total'],
        done_tasks=metrics['done'],
        overdue_tasks=metrics['overdue'],
        blocked_tasks=metrics['blocked'],
        phases=_phase_rows(session, project.id, day),
        schedule_conflicts=_conflicts(session, project),
        events=_events(session, project.id, None),
    )


def update_project(session: Session, project_id: int, payload: ProjectUpdate, actor: User) -> ProjectDetail:
    project = _load_project(session, project_id)
    owner = _require_user(session, payload.owner_id, 'Responsável')
    if project.owner_id != owner.id:
        previous = project.owner.name
        project.owner_id = owner.id
        project.owner = owner
        _record(
            session,
            project_id=project.id,
            actor_id=actor.id,
            event_type='project_owner_changed',
            old_value=previous,
            new_value=owner.name,
        )
    if project.due_date != payload.due_date:
        _record(
            session,
            project_id=project.id,
            actor_id=actor.id,
            event_type='project_due_date_changed',
            old_value=project.due_date.isoformat() if project.due_date else None,
            new_value=payload.due_date.isoformat() if payload.due_date else None,
        )
        project.due_date = payload.due_date
    project.name = payload.name
    project.description = payload.description
    project.start_date = payload.start_date
    _touch(project)
    session.flush()
    return get_project(session, project.id)


def change_status(session: Session, project_id: int, payload: StatusChange, actor: User) -> ProjectDetail:
    project = _load_project(session, project_id)
    if payload.status == project.status:
        return get_project(session, project.id)
    allowed = STATUS_TRANSITIONS[project.status]
    if payload.status not in allowed:
        raise HTTPException(status_code=422, detail='Essa mudança de status não está disponível.')
    if payload.status == 'concluido' and not payload.confirm_open_tasks:
        open_tasks = session.scalar(
            select(func.count(Task.id))
            .join(Phase, Phase.id == Task.phase_id)
            .where(Phase.project_id == project.id, Task.status != 'concluida')
        )
        open_count = _as_int(open_tasks)
        if open_count:
            raise HTTPException(status_code=409, detail={
                'code': 'open_tasks',
                'open_task_count': open_count,
                'message': f'Ainda há {open_count} tarefas abertas.',
            })
    previous = project.status
    project.status = payload.status
    _touch(project)
    _record(
        session,
        project_id=project.id,
        actor_id=actor.id,
        event_type='project_status_changed',
        old_value=previous,
        new_value=payload.status,
    )
    session.flush()
    return get_project(session, project.id)


def delete_project(session: Session, project_id: int) -> None:
    project = session.get(Project, project_id)
    if project is None:
        raise _missing('Projeto')
    if project.status != 'rascunho':
        raise HTTPException(
            status_code=409,
            detail='Só um rascunho pode ser apagado. Conclua ou cancele o projeto.',
        )
    session.delete(project)


def create_phase(session: Session, project_id: int, payload: PhaseCreate) -> PhaseDetail:
    project = _load_project(session, project_id)
    last = session.scalar(select(func.max(Phase.position)).where(Phase.project_id == project.id))
    phase = Phase(
        project_id=project.id,
        name=payload.name,
        position=0 if last is None else last + 1,
        status='nao_iniciada',
        start_date=payload.start_date,
        due_date=payload.due_date,
    )
    session.add(phase)
    _touch(project)
    session.flush()
    return get_phase(session, phase.id)


def update_phase(session: Session, phase_id: int, payload: PhaseUpdate) -> PhaseDetail:
    phase = session.get(Phase, phase_id)
    if phase is None:
        raise _missing('Fase')
    project = _load_project(session, phase.project_id)
    phase.name = payload.name
    phase.status = payload.status
    phase.start_date = payload.start_date
    phase.due_date = payload.due_date
    _touch(project)
    session.flush()
    return get_phase(session, phase.id)


def reorder_phases(session: Session, project_id: int, ordered_ids: list[int]) -> ProjectDetail:
    project = _load_project(session, project_id)
    phases = list(session.scalars(select(Phase).where(Phase.project_id == project.id)))
    _reorder(session, phases, ordered_ids)
    _touch(project)
    session.flush()
    return get_project(session, project.id)


def get_phase(session: Session, phase_id: int, day: date | None = None) -> PhaseDetail:
    day = day or clock_today()
    phase = session.scalar(
        select(Phase)
        .options(selectinload(Phase.tasks).selectinload(Task.assignee))
        .where(Phase.id == phase_id)
    )
    if phase is None:
        raise _missing('Fase')
    project = _load_project(session, phase.project_id)
    metrics = _metrics(session, project, day)
    tasks = [_task_item(task, phase, day) for task in sorted(phase.tasks, key=lambda item: item.position)]
    done = sum(1 for task in tasks if task.status == 'concluida')
    overdue = sum(1 for task in tasks if task.overdue)
    return PhaseDetail(
        **_context(project, metrics),
        id=phase.id,
        name=phase.name,
        status=phase.status,
        progress=progress_percent(done, len(tasks), empty_is_complete=phase.status == 'concluida'),
        start_date=phase.start_date,
        due_date=phase.due_date,
        total_tasks=len(tasks),
        done_tasks=done,
        overdue_tasks=overdue,
        tasks=tasks,
    )


def create_task(session: Session, phase_id: int, payload: TaskCreate, actor: User) -> TaskDetail:
    phase = session.get(Phase, phase_id)
    if phase is None:
        raise _missing('Fase')
    project = _load_project(session, phase.project_id)
    last = session.scalar(select(func.max(Task.position)).where(Task.phase_id == phase.id))
    task = Task(
        phase_id=phase.id,
        title=payload.title,
        description='',
        position=0 if last is None else last + 1,
        status='a_fazer',
    )
    session.add(task)
    session.flush()
    _record(
        session,
        project_id=project.id,
        task_id=task.id,
        actor_id=actor.id,
        event_type='task_created',
        new_value=task.title,
    )
    _touch(project)
    session.flush()
    return get_task(session, task.id)


def reorder_tasks(session: Session, phase_id: int, ordered_ids: list[int]) -> PhaseDetail:
    phase = session.get(Phase, phase_id)
    if phase is None:
        raise _missing('Fase')
    project = _load_project(session, phase.project_id)
    tasks = list(session.scalars(select(Task).where(Task.phase_id == phase.id)))
    _reorder(session, tasks, ordered_ids)
    _touch(project)
    session.flush()
    return get_phase(session, phase.id)


def list_project_tasks(session: Session, project_id: int, filtro: str, day: date | None = None) -> list[TaskListItem]:
    day = day or clock_today()
    _load_project(session, project_id)
    statement = (
        select(Task, Phase)
        .join(Phase, Phase.id == Task.phase_id)
        .options(selectinload(Task.assignee))
        .where(Phase.project_id == project_id)
        .order_by(Phase.position, Task.position)
    )
    if filtro == 'atrasadas':
        statement = statement.where(_overdue_condition(day))
    elif filtro == 'bloqueadas':
        statement = statement.where(Task.status == 'bloqueada')
    elif filtro == 'concluidas':
        statement = statement.where(Task.status == 'concluida')
    elif filtro == 'abertas':
        statement = statement.where(Task.status != 'concluida')
    elif filtro != 'todas':
        raise HTTPException(status_code=422, detail='Filtro de tarefas inválido.')
    return [_task_item(task, phase, day) for task, phase in session.execute(statement)]


def get_task(session: Session, task_id: int, day: date | None = None) -> TaskDetail:
    day = day or clock_today()
    task = session.scalar(
        select(Task).options(selectinload(Task.assignee), selectinload(Task.phase)).where(Task.id == task_id)
    )
    if task is None:
        raise _missing('Tarefa')
    project = _load_project(session, task.phase.project_id)
    metrics = _metrics(session, project, day)
    phase_tasks = list(session.scalars(select(Task.status).where(Task.phase_id == task.phase_id)))
    phase_done = sum(1 for status in phase_tasks if status == 'concluida')
    return TaskDetail(
        **_context(project, metrics),
        id=task.id,
        phase_id=task.phase.id,
        phase_name=task.phase.name,
        phase_progress=progress_percent(
            phase_done,
            len(phase_tasks),
            empty_is_complete=task.phase.status == 'concluida',
        ),
        phase_total_tasks=len(phase_tasks),
        phase_done_tasks=phase_done,
        title=task.title,
        description=task.description,
        status=task.status,
        assignee=_user_out(task.assignee) if task.assignee is not None else None,
        due_date=task.due_date,
        blocked_reason=task.blocked_reason,
        overdue=task_is_overdue(task.due_date, task.status, day),
        events=_events(session, project.id, task.id),
    )


def update_task(session: Session, task_id: int, payload: TaskUpdate, actor: User) -> TaskDetail:
    task = session.scalar(select(Task).options(selectinload(Task.assignee), selectinload(Task.phase)).where(Task.id == task_id))
    if task is None:
        raise _missing('Tarefa')
    project = _load_project(session, task.phase.project_id)
    assignee = None
    if payload.assignee_id is not None:
        assignee = _require_user(session, payload.assignee_id, 'Responsável')
    if task.status != payload.status:
        _record(
            session,
            project_id=project.id,
            task_id=task.id,
            actor_id=actor.id,
            event_type='task_status_changed',
            old_value=task.status,
            new_value=payload.status,
        )
    previous_assignee = task.assignee_id
    if previous_assignee != payload.assignee_id:
        _record(
            session,
            project_id=project.id,
            task_id=task.id,
            actor_id=actor.id,
            event_type='task_assignee_changed',
            old_value=task.assignee.name if task.assignee is not None else None,
            new_value=assignee.name if assignee is not None else None,
        )
    if task.due_date != payload.due_date:
        _record(
            session,
            project_id=project.id,
            task_id=task.id,
            actor_id=actor.id,
            event_type='task_due_date_changed',
            old_value=task.due_date.isoformat() if task.due_date else None,
            new_value=payload.due_date.isoformat() if payload.due_date else None,
        )
    task.title = payload.title
    task.description = payload.description
    task.status = payload.status
    task.assignee_id = payload.assignee_id
    task.assignee = assignee
    task.due_date = payload.due_date
    task.blocked_reason = payload.blocked_reason
    _touch(project)
    session.flush()
    return get_task(session, task.id)
