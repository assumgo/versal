from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.core.dependencies import CurrentUser, Database
from app.schemas.projects import (
    Health,
    PhaseCreate,
    PhaseDetail,
    PhaseUpdate,
    ProjectCreate,
    ProjectDetail,
    ProjectListResponse,
    ProjectStatus,
    ProjectUpdate,
    Reorder,
    StatusChange,
    TaskCreate,
    TaskDetail,
    TaskFilter,
    TaskListItem,
    TaskUpdate,
    TemplateOut,
    TemplatePhaseOut,
)
from app.services.catalog import list_templates
from app.services import projects as service

router = APIRouter(prefix='/api', tags=['projects'])


@router.get('/templates', response_model=list[TemplateOut])
def templates(_user: CurrentUser, db: Database) -> list[TemplateOut]:
    rows = [
        TemplateOut(
            key=template.key,
            name=template.name,
            phases=[
                TemplatePhaseOut(
                    name=phase.name,
                    tasks=[task.title for task in sorted(phase.tasks, key=lambda item: item.position)],
                )
                for phase in sorted(template.phases, key=lambda item: item.position)
            ],
        )
        for template in list_templates(db)
    ]
    db.commit()
    return rows


@router.get('/projects', response_model=ProjectListResponse)
def list_projects(
    _user: CurrentUser,
    db: Database,
    q: Annotated[str | None, Query()] = None,
    owner_id: Annotated[int | None, Query()] = None,
    status: Annotated[ProjectStatus | None, Query()] = None,
    health: Annotated[Health | None, Query()] = None,
) -> ProjectListResponse:
    result = service.list_projects(db, query=q, owner_id=owner_id, status=status, health=health)
    db.commit()
    return result


@router.post('/projects', response_model=ProjectDetail, status_code=201)
def create_project(payload: ProjectCreate, user: CurrentUser, db: Database) -> ProjectDetail:
    result = service.create_project(db, payload, user)
    db.commit()
    return result


@router.get('/projects/{project_id}', response_model=ProjectDetail)
def get_project(project_id: int, _user: CurrentUser, db: Database) -> ProjectDetail:
    return service.get_project(db, project_id)


@router.put('/projects/{project_id}', response_model=ProjectDetail)
def update_project(project_id: int, payload: ProjectUpdate, user: CurrentUser, db: Database) -> ProjectDetail:
    result = service.update_project(db, project_id, payload, user)
    db.commit()
    return result


@router.post('/projects/{project_id}/status', response_model=ProjectDetail)
def change_status(project_id: int, payload: StatusChange, user: CurrentUser, db: Database) -> ProjectDetail:
    result = service.change_status(db, project_id, payload, user)
    db.commit()
    return result


@router.delete('/projects/{project_id}', status_code=204)
def delete_project(project_id: int, _user: CurrentUser, db: Database) -> Response:
    service.delete_project(db, project_id)
    db.commit()
    return Response(status_code=204)


@router.post('/projects/{project_id}/phases', response_model=PhaseDetail, status_code=201)
def create_phase(project_id: int, payload: PhaseCreate, _user: CurrentUser, db: Database) -> PhaseDetail:
    result = service.create_phase(db, project_id, payload)
    db.commit()
    return result


@router.post('/projects/{project_id}/phases/reorder', response_model=ProjectDetail)
def reorder_phases(project_id: int, payload: Reorder, _user: CurrentUser, db: Database) -> ProjectDetail:
    result = service.reorder_phases(db, project_id, payload.ids)
    db.commit()
    return result


@router.get('/projects/{project_id}/tasks', response_model=list[TaskListItem])
def list_tasks(
    project_id: int,
    _user: CurrentUser,
    db: Database,
    filtro: Annotated[TaskFilter, Query()] = 'todas',
) -> list[TaskListItem]:
    return service.list_project_tasks(db, project_id, filtro)


@router.get('/phases/{phase_id}', response_model=PhaseDetail)
def get_phase(phase_id: int, _user: CurrentUser, db: Database) -> PhaseDetail:
    return service.get_phase(db, phase_id)


@router.put('/phases/{phase_id}', response_model=PhaseDetail)
def update_phase(phase_id: int, payload: PhaseUpdate, _user: CurrentUser, db: Database) -> PhaseDetail:
    result = service.update_phase(db, phase_id, payload)
    db.commit()
    return result


@router.post('/phases/{phase_id}/tasks', response_model=TaskDetail, status_code=201)
def create_task(phase_id: int, payload: TaskCreate, user: CurrentUser, db: Database) -> TaskDetail:
    result = service.create_task(db, phase_id, payload, user)
    db.commit()
    return result


@router.post('/phases/{phase_id}/tasks/reorder', response_model=PhaseDetail)
def reorder_tasks(phase_id: int, payload: Reorder, _user: CurrentUser, db: Database) -> PhaseDetail:
    result = service.reorder_tasks(db, phase_id, payload.ids)
    db.commit()
    return result


@router.get('/tasks/{task_id}', response_model=TaskDetail)
def get_task(task_id: int, _user: CurrentUser, db: Database) -> TaskDetail:
    return service.get_task(db, task_id)


@router.put('/tasks/{task_id}', response_model=TaskDetail)
def update_task(task_id: int, payload: TaskUpdate, user: CurrentUser, db: Database) -> TaskDetail:
    result = service.update_task(db, task_id, payload, user)
    db.commit()
    return result
