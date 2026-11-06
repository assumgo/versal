from sqlalchemy import Boolean, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdentityMixin, TimestampMixin


class Room(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'rooms'
    name: Mapped[str] = mapped_column(String(120), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
