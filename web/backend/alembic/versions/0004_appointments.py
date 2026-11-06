"""Add company appointments shown on the dashboard calendar.

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'appointments',
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('starts_at', sa.Time(), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_appointments_company_id_companies'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_appointments')),
    )
    op.create_index(op.f('ix_appointments_company_id'), 'appointments', ['company_id'], unique=False)
    op.create_index('ix_appointments_company_date', 'appointments', ['company_id', 'scheduled_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_appointments_company_date', table_name='appointments')
    op.drop_index(op.f('ix_appointments_company_id'), table_name='appointments')
    op.drop_table('appointments')
