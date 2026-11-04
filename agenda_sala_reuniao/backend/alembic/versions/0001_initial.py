"""Initial agenda schema.

Revision ID: 0001_initial
Revises:
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0001_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('email', sa.String(254), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('family_id', sa.Uuid(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_refresh_tokens_user_id_users', ondelete='RESTRICT'),
        sa.UniqueConstraint('token_hash', name='uq_refresh_tokens_token_hash'),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_family_id', 'refresh_tokens', ['family_id'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_table(
        'rooms',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('location', sa.String(120), server_default=sa.text("''"), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('name', name='uq_rooms_name'),
        sa.CheckConstraint('capacity >= 1', name='ck_rooms_capacity_positive'),
    )
    op.create_table(
        'reservations',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('room_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], name='fk_reservations_room_id_rooms', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_reservations_user_id_users', ondelete='RESTRICT'),
        sa.CheckConstraint('ends_at > starts_at', name='ck_reservations_ends_after_start'),
    )
    op.create_index('ix_reservations_room_id', 'reservations', ['room_id'])
    op.create_index('ix_reservations_user_id', 'reservations', ['user_id'])
    op.execute(
        "ALTER TABLE reservations ADD CONSTRAINT ex_reservations_no_overlap "
        "EXCLUDE USING gist (room_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&)"
    )


def downgrade() -> None:
    op.drop_table('reservations')
    op.drop_table('rooms')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
