"""Add nullable source metadata to payroll imports.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('imports', sa.Column('arquivo_sha256', sa.String(length=64), nullable=True))
    op.add_column('imports', sa.Column('arquivo_bytes', sa.Integer(), nullable=True))
    op.add_column('imports', sa.Column('quantidade_colaboradores', sa.Integer(), nullable=True))
    op.add_column('imports', sa.Column('quantidade_rubricas', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('imports', 'quantidade_rubricas')
    op.drop_column('imports', 'quantidade_colaboradores')
    op.drop_column('imports', 'arquivo_bytes')
    op.drop_column('imports', 'arquivo_sha256')
