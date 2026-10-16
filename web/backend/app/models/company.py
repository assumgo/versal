from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdentityMixin, TimestampMixin


class Company(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'companies'
    name: Mapped[str] = mapped_column(String(255))
    cnpj: Mapped[str] = mapped_column(String(14), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    memberships: Mapped[list['UserCompany']] = relationship(back_populates='company', passive_deletes='all')
    employees: Mapped[list['Employee']] = relationship(back_populates='company', passive_deletes='all')


class Employee(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'employees'
    __table_args__ = (
        UniqueConstraint('company_id', 'registration'),
        UniqueConstraint('company_id', 'cpf'),
        UniqueConstraint('company_id', 'id'),
    )
    company_id: Mapped[UUID] = mapped_column(ForeignKey('companies.id', ondelete='RESTRICT'), index=True)
    registration: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(255))
    cpf: Mapped[str] = mapped_column(String(11))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    company: Mapped[Company] = relationship(back_populates='employees')
