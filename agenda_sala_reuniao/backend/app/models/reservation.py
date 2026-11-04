from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, column, func
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdentityMixin, TimestampMixin
from app.models.room import Room
from app.models.user import User


class Reservation(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'reservations'
    __table_args__ = (
        CheckConstraint('ends_at > starts_at', name='ends_after_start'),
        ExcludeConstraint(
            (column('room_id'), '='),
            (func.tstzrange(column('starts_at'), column('ends_at'), '[)'), '&&'),
            using='gist',
            name='ex_reservations_no_overlap',
        ),
    )
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id', ondelete='RESTRICT'), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), index=True)
    title: Mapped[str] = mapped_column(String(120))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    room: Mapped[Room] = relationship()
    organizer: Mapped[User] = relationship()
