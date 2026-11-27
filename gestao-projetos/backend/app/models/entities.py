from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

PROJECT_STATUSES = ('rascunho', 'em_andamento', 'pausado', 'concluido', 'cancelado')
PHASE_STATUSES = ('nao_iniciada', 'em_andamento', 'concluida')
TASK_STATUSES = ('a_fazer', 'em_andamento', 'bloqueada', 'concluida')


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectTemplate(Base):
    __tablename__ = 'project_templates'

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    phases: Mapped[list['TemplatePhase']] = relationship(
        back_populates='template',
        cascade='all, delete-orphan',
        order_by='TemplatePhase.position',
    )


class TemplatePhase(Base):
    __tablename__ = 'template_phases'
    __table_args__ = (UniqueConstraint('template_id', 'position'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey('project_templates.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[int]
    template: Mapped[ProjectTemplate] = relationship(back_populates='phases')
    tasks: Mapped[list['TemplateTask']] = relationship(
        back_populates='phase',
        cascade='all, delete-orphan',
        order_by='TemplateTask.position',
    )


class TemplateTask(Base):
    __tablename__ = 'template_tasks'
    __table_args__ = (UniqueConstraint('template_phase_id', 'position'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    template_phase_id: Mapped[int] = mapped_column(ForeignKey('template_phases.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    position: Mapped[int]
    phase: Mapped[TemplatePhase] = relationship(back_populates='tasks')


class Project(Base):
    __tablename__ = 'projects'
    __table_args__ = (
        CheckConstraint(
            "status IN ('rascunho', 'em_andamento', 'pausado', 'concluido', 'cancelado')",
            name='status',
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default='', server_default='')
    status: Mapped[str] = mapped_column(String(20))
    start_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    owner: Mapped[User] = relationship()
    phases: Mapped[list['Phase']] = relationship(
        back_populates='project',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='Phase.position',
    )
    events: Mapped[list['ActivityEvent']] = relationship(
        back_populates='project',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )


class Phase(Base):
    __tablename__ = 'phases'
    __table_args__ = (
        UniqueConstraint('project_id', 'position'),
        CheckConstraint(
            "status IN ('nao_iniciada', 'em_andamento', 'concluida')",
            name='status',
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default='nao_iniciada', server_default='nao_iniciada')
    start_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    project: Mapped[Project] = relationship(back_populates='phases')
    tasks: Mapped[list['Task']] = relationship(
        back_populates='phase',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='Task.position',
    )


class Task(Base):
    __tablename__ = 'tasks'
    __table_args__ = (
        UniqueConstraint('phase_id', 'position'),
        CheckConstraint(
            "status IN ('a_fazer', 'em_andamento', 'bloqueada', 'concluida')",
            name='status',
        ),
        CheckConstraint(
            "(status != 'bloqueada') OR (blocked_reason IS NOT NULL AND length(trim(blocked_reason)) > 0)",
            name='blocked_reason',
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey('phases.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default='', server_default='')
    position: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default='a_fazer', server_default='a_fazer')
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), index=True)
    due_date: Mapped[date | None] = mapped_column(Date)
    blocked_reason: Mapped[str | None] = mapped_column(String(280))
    phase: Mapped[Phase] = relationship(back_populates='tasks')
    assignee: Mapped[User | None] = relationship()


class ActivityEvent(Base):
    __tablename__ = 'activity_events'

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE'), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    old_value: Mapped[str | None] = mapped_column(String(200))
    new_value: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    project: Mapped[Project] = relationship(back_populates='events')
    actor: Mapped[User] = relationship()
