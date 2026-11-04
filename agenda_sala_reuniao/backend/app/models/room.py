from sqlalchemy import Boolean, CheckConstraint, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdentityMixin, TimestampMixin


class Room(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'rooms'
    __table_args__ = (CheckConstraint('capacity >= 1', name='capacity_positive'),)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    location: Mapped[str] = mapped_column(String(120), server_default=text("''"))
    capacity: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
