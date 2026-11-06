"""Add bookable rooms to reservations.

Revision ID: 0006
Revises: 0005
"""
import sqlalchemy as sa
from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'rooms',
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_rooms')),
        sa.UniqueConstraint('name', name=op.f('uq_rooms_name')),
    )
    op.execute("INSERT INTO rooms (id, name) VALUES (1, 'Sala1'), (2, 'Sala2'), (3, 'Sala3')")
    op.execute("SELECT setval(pg_get_serial_sequence('rooms', 'id'), (SELECT MAX(id) FROM rooms))")
    op.add_column('appointments', sa.Column('room_id', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_appointments_room_id'), 'appointments', ['room_id'])
    op.create_foreign_key(op.f('fk_appointments_room_id_rooms'), 'appointments', 'rooms', ['room_id'], ['id'], ondelete='RESTRICT')
    op.execute(
        "UPDATE appointments AS appointment "
        "SET room_id = room.id, title = substr(appointment.title, length(room.name) + 4) "
        "FROM rooms AS room "
        "WHERE appointment.company_id IS NULL AND appointment.title LIKE room.name || ' · %'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE appointments AS appointment "
        "SET title = room.name || ' · ' || appointment.title "
        "FROM rooms AS room "
        "WHERE appointment.room_id = room.id AND appointment.title NOT LIKE room.name || ' · %'"
    )
    op.drop_constraint(op.f('fk_appointments_room_id_rooms'), 'appointments', type_='foreignkey')
    op.drop_index(op.f('ix_appointments_room_id'), table_name='appointments')
    op.drop_column('appointments', 'room_id')
    op.drop_table('rooms')
