from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdentityMixin, TimestampMixin


class Role(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'roles'
    name: Mapped[str] = mapped_column(String(40), unique=True)
    users: Mapped[list['User']] = relationship(back_populates='role')


class User(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'users'
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[UUID] = mapped_column(ForeignKey('roles.id', ondelete='RESTRICT'), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    role: Mapped[Role] = relationship(back_populates='users')
    memberships: Mapped[list['UserCompany']] = relationship(back_populates='user', passive_deletes='all')
    refresh_tokens: Mapped[list['RefreshToken']] = relationship(back_populates='user', passive_deletes='all')


class UserCompany(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'user_companies'
    __table_args__ = (UniqueConstraint('user_id', 'company_id'),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'))
    company_id: Mapped[UUID] = mapped_column(ForeignKey('companies.id', ondelete='RESTRICT'), index=True)
    user: Mapped[User] = relationship(back_populates='memberships')
    company: Mapped['Company'] = relationship(back_populates='memberships')


class RefreshToken(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'refresh_tokens'
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    family_id: Mapped[UUID] = mapped_column(index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship(back_populates='refresh_tokens')
