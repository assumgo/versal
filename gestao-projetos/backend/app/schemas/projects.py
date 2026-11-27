from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ProjectStatus = Literal['rascunho', 'em_andamento', 'pausado', 'concluido', 'cancelado']
PhaseStatus = Literal['nao_iniciada', 'em_andamento', 'concluida']
TaskStatus = Literal['a_fazer', 'em_andamento', 'bloqueada', 'concluida']
TemplateKey = Literal['rack', 'system']
TaskFilter = Literal['todas', 'abertas', 'concluidas', 'atrasadas', 'bloqueadas']
Health = Literal['no_prazo', 'atencao', 'atrasado', 'pausado', 'concluido', 'cancelado']


def _clean(value: str) -> str:
    return value.strip()


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if ' ' in email or email.count('@') != 1 or email.startswith('@') or email.endswith('@'):
        raise ValueError('E-mail inválido')
    local, domain = email.split('@')
    if not local or '.' not in domain or domain.startswith('.') or domain.endswith('.'):
        raise ValueError('E-mail inválido')
    return email


def _check_dates(start_date: date | None, due_date: date | None) -> None:
    if start_date is not None and due_date is not None and start_date > due_date:
        raise ValueError('A data de início precisa ser anterior ou igual ao prazo')


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=200)

    @field_validator('email')
    @classmethod
    def email_value(cls, value: str) -> str:
        return _normalize_email(value)


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=200)

    @field_validator('name')
    @classmethod
    def name_value(cls, value: str) -> str:
        cleaned = _clean(value)
        if not cleaned:
            raise ValueError('Informe o nome')
        return cleaned

    @field_validator('email')
    @classmethod
    def email_value(cls, value: str) -> str:
        return _normalize_email(value)


class UserOut(BaseModel):
    id: int
    name: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    user: UserOut


class TemplatePhaseOut(BaseModel):
    name: str
    tasks: list[str]


class TemplateOut(BaseModel):
    key: str
    name: str
    phases: list[TemplatePhaseOut]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=4000)
    owner_id: int
    start_date: date | None = None
    due_date: date | None = None
    template_key: TemplateKey | None = None
    status: Literal['rascunho', 'em_andamento'] = 'em_andamento'

    @field_validator('name', 'description')
    @classmethod
    def text_value(cls, value: str) -> str:
        return _clean(value)

    @model_validator(mode='after')
    def dates(self) -> 'ProjectCreate':
        if not self.name:
            raise ValueError('Informe o nome do projeto')
        _check_dates(self.start_date, self.due_date)
        return self


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=4000)
    owner_id: int
    start_date: date | None = None
    due_date: date | None = None

    @field_validator('name', 'description')
    @classmethod
    def text_value(cls, value: str) -> str:
        return _clean(value)

    @model_validator(mode='after')
    def dates(self) -> 'ProjectUpdate':
        if not self.name:
            raise ValueError('Informe o nome do projeto')
        _check_dates(self.start_date, self.due_date)
        return self


class StatusChange(BaseModel):
    status: ProjectStatus
    confirm_open_tasks: bool = False


class PhaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    start_date: date | None = None
    due_date: date | None = None

    @field_validator('name')
    @classmethod
    def name_value(cls, value: str) -> str:
        cleaned = _clean(value)
        if not cleaned:
            raise ValueError('Informe o nome da fase')
        return cleaned

    @model_validator(mode='after')
    def dates(self) -> 'PhaseCreate':
        _check_dates(self.start_date, self.due_date)
        return self


class PhaseUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    status: PhaseStatus
    start_date: date | None = None
    due_date: date | None = None

    @field_validator('name')
    @classmethod
    def name_value(cls, value: str) -> str:
        cleaned = _clean(value)
        if not cleaned:
            raise ValueError('Informe o nome da fase')
        return cleaned

    @model_validator(mode='after')
    def dates(self) -> 'PhaseUpdate':
        _check_dates(self.start_date, self.due_date)
        return self


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator('title')
    @classmethod
    def title_value(cls, value: str) -> str:
        cleaned = _clean(value)
        if not cleaned:
            raise ValueError('Informe o título da tarefa')
        return cleaned


class TaskUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=4000)
    status: TaskStatus
    assignee_id: int | None = None
    due_date: date | None = None
    blocked_reason: str | None = Field(default=None, max_length=280)

    @field_validator('title', 'description')
    @classmethod
    def text_value(cls, value: str) -> str:
        return _clean(value)

    @field_validator('blocked_reason')
    @classmethod
    def reason_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean(value)
        return cleaned or None

    @model_validator(mode='after')
    def blocked(self) -> 'TaskUpdate':
        if not self.title:
            raise ValueError('Informe o título da tarefa')
        if self.status == 'bloqueada' and not self.blocked_reason:
            raise ValueError('Informe o motivo do bloqueio')
        if self.status != 'bloqueada':
            self.blocked_reason = None
        return self


class Reorder(BaseModel):
    ids: list[int] = Field(min_length=1)


class ActivityEventOut(BaseModel):
    id: int
    event_type: str
    old_value: str | None
    new_value: str | None
    actor_name: str
    created_at: datetime
    task_id: int | None = None


class PhaseListItem(BaseModel):
    id: int
    name: str
    status: str
    position: int
    start_date: date | None
    due_date: date | None
    progress: int
    total_tasks: int
    done_tasks: int
    overdue_tasks: int


class TaskConflict(BaseModel):
    id: int
    title: str
    phase_id: int
    phase_name: str
    due_date: date


class ProjectContext(BaseModel):
    project_id: int
    project_name: str
    project_status: str
    project_health: str
    project_progress: int
    project_due_date: date | None
    project_owner: UserOut


class ProjectListItem(BaseModel):
    id: int
    name: str
    status: str
    health: str
    owner: UserOut
    due_date: date | None
    progress: int
    next_overdue_on: date | None
    total_tasks: int
    done_tasks: int


class ProjectSummary(BaseModel):
    ativos: int
    no_prazo: int
    atencao: int
    atrasados: int


class ProjectListResponse(BaseModel):
    today: date
    summary: ProjectSummary
    projects: list[ProjectListItem]


class ProjectDetail(ProjectContext):
    description: str
    start_date: date | None
    total_tasks: int
    done_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    phases: list[PhaseListItem]
    schedule_conflicts: list[TaskConflict]
    events: list[ActivityEventOut]


class TaskListItem(BaseModel):
    id: int
    phase_id: int
    phase_name: str
    title: str
    status: str
    assignee: UserOut | None
    due_date: date | None
    overdue: bool
    blocked_reason: str | None
    position: int


class PhaseDetail(ProjectContext):
    id: int
    name: str
    status: str
    progress: int
    start_date: date | None
    due_date: date | None
    total_tasks: int
    done_tasks: int
    overdue_tasks: int
    tasks: list[TaskListItem]


class TaskDetail(ProjectContext):
    id: int
    phase_id: int
    phase_name: str
    phase_progress: int
    phase_total_tasks: int
    phase_done_tasks: int
    title: str
    description: str
    status: str
    assignee: UserOut | None
    due_date: date | None
    blocked_reason: str | None
    overdue: bool
    events: list[ActivityEventOut]
