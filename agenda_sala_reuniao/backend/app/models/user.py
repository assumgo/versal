from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdentityMixin, TimestampMixin


class User(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'users'
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    must_change_password: Mapped[bool] = mapped_column(Boolean, server_default=text('false'), default=False)
    refresh_tokens: Mapped[list['RefreshToken']] = relationship(back_populates='user')


class RefreshToken(IdentityMixin, Base):
    __tablename__ = 'refresh_tokens'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    family_id: Mapped[UUID] = mapped_column(index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text('now()'))
    user: Mapped[User] = relationship(back_populates='refresh_tokens')
