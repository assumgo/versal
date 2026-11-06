"""Separate room reservations from company payroll appointments.

Revision ID: 0005
Revises: 0004
"""
import sqlalchemy as sa
from alembic import op

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('appointments', sa.Column('ends_at', sa.Time(), nullable=True))
    op.execute(
        "UPDATE appointments SET ends_at = CASE "
        "WHEN starts_at <= TIME '22:00:00' THEN starts_at + INTERVAL '1 hour' "
        "ELSE TIME '23:59:00' END"
    )
    op.alter_column('appointments', 'ends_at', existing_type=sa.Time(), nullable=False)
    op.alter_column('appointments', 'company_id', existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    op.execute('DELETE FROM appointments WHERE company_id IS NULL')
    op.alter_column('appointments', 'company_id', existing_type=sa.BigInteger(), nullable=False)
    op.drop_column('appointments', 'ends_at')
