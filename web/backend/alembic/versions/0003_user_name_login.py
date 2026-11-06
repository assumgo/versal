"""Add user name and case-insensitive login.

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def _initial_login(email: str, user_id: int, used: set[str]) -> str:
    candidate = email.strip()
    if len(candidate) < 3 or len(candidate) > 80 or any(character.isspace() for character in candidate):
        candidate = f'user{user_id}'[:80]
    base = candidate
    suffix = 0
    while candidate.lower() in used:
        suffix += 1
        tail = f'-{user_id}' if suffix == 1 else f'-{user_id}-{suffix}'
        candidate = f'{base[:80 - len(tail)]}{tail}'
    used.add(candidate.lower())
    return candidate


def upgrade() -> None:
    op.add_column('users', sa.Column('name', sa.String(length=120), nullable=True))
    op.add_column('users', sa.Column('login', sa.String(length=80), nullable=True))
    connection = op.get_bind()
    rows = connection.execute(sa.text('SELECT id, email FROM users ORDER BY id')).all()
    used: set[str] = set()
    for row in rows:
        connection.execute(
            sa.text('UPDATE users SET login = :login WHERE id = :id'),
            {'login': _initial_login(row.email, row.id, used), 'id': row.id},
        )
    op.create_index('uq_users_login_lower', 'users', [sa.text('lower(login)')], unique=True)


def downgrade() -> None:
    op.drop_index('uq_users_login_lower', table_name='users')
    op.drop_column('users', 'login')
    op.drop_column('users', 'name')
