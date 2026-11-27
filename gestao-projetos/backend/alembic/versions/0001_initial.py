"""Initial project management schema."""

from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_table(
        'project_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('key', sa.String(length=40), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.UniqueConstraint('key', name='uq_project_templates_key'),
    )
    op.create_table(
        'template_phases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('project_templates.id', ondelete='CASCADE', name='fk_template_phases_template_id_project_templates'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.UniqueConstraint('template_id', 'position', name='uq_template_phases_template_id_position'),
    )
    op.create_index('ix_template_phases_template_id', 'template_phases', ['template_id'])
    op.create_table(
        'template_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('template_phase_id', sa.Integer(), sa.ForeignKey('template_phases.id', ondelete='CASCADE', name='fk_template_tasks_template_phase_id_template_phases'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.UniqueConstraint('template_phase_id', 'position', name='uq_template_tasks_template_phase_id_position'),
    )
    op.create_index('ix_template_tasks_template_phase_id', 'template_tasks', ['template_phase_id'])
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_projects_owner_id_users'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('rascunho', 'em_andamento', 'pausado', 'concluido', 'cancelado')",
            name='status',
        ),
    )
    op.create_index('ix_projects_owner_id', 'projects', ['owner_id'])
    op.create_table(
        'phases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE', name='fk_phases_project_id_projects'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='nao_iniciada', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.CheckConstraint(
            "status IN ('nao_iniciada', 'em_andamento', 'concluida')",
            name='status',
        ),
        sa.UniqueConstraint('project_id', 'position', name='uq_phases_project_id_position'),
    )
    op.create_index('ix_phases_project_id', 'phases', ['project_id'])
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('phase_id', sa.Integer(), sa.ForeignKey('phases.id', ondelete='CASCADE', name='fk_tasks_phase_id_phases'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='a_fazer', nullable=False),
        sa.Column('assignee_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_tasks_assignee_id_users'), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('blocked_reason', sa.String(length=280), nullable=True),
        sa.CheckConstraint(
            "status IN ('a_fazer', 'em_andamento', 'bloqueada', 'concluida')",
            name='status',
        ),
        sa.CheckConstraint(
            "(status != 'bloqueada') OR (blocked_reason IS NOT NULL AND length(trim(blocked_reason)) > 0)",
            name='blocked_reason',
        ),
        sa.UniqueConstraint('phase_id', 'position', name='uq_tasks_phase_id_position'),
    )
    op.create_index('ix_tasks_phase_id', 'tasks', ['phase_id'])
    op.create_index('ix_tasks_assignee_id', 'tasks', ['assignee_id'])
    op.create_table(
        'activity_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE', name='fk_activity_events_project_id_projects'), nullable=False),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE', name='fk_activity_events_task_id_tasks'), nullable=True),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_activity_events_actor_id_users'), nullable=False),
        sa.Column('event_type', sa.String(length=40), nullable=False),
        sa.Column('old_value', sa.String(length=200), nullable=True),
        sa.Column('new_value', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_activity_events_project_id', 'activity_events', ['project_id'])
    op.create_index('ix_activity_events_task_id', 'activity_events', ['task_id'])
    op.create_index('ix_activity_events_actor_id', 'activity_events', ['actor_id'])


def downgrade() -> None:
    op.drop_table('activity_events')
    op.drop_table('tasks')
    op.drop_table('phases')
    op.drop_table('projects')
    op.drop_table('template_tasks')
    op.drop_table('template_phases')
    op.drop_table('project_templates')
    op.drop_table('users')
