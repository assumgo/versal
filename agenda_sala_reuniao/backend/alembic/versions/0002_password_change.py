"""Require a password change on the next access.

Revision ID: 0002_password_change
Revises: 0001_initial
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0002_password_change'
down_revision: Union[str, Sequence[str], None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('must_change_password', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('users', 'must_change_password')
