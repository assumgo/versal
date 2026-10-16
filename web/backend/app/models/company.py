from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.models.base import Base, IdentityMixin, TimestampMixin


class Company(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'companies'
    codigo_siagri: Mapped[str | None] = mapped_column(Text)
    razao: Mapped[str | None] = mapped_column(Text)
    fantasia: Mapped[str | None] = mapped_column(Text)
    cnpj: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text, server_default='Ativa')
    name = synonym('razao')
    memberships: Mapped[list['UserCompany']] = relationship(back_populates='company', passive_deletes='all')
    employees: Mapped[list['Employee']] = relationship(back_populates='company', passive_deletes='all')


class Employee(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'employees'
    __table_args__ = (
        Index('idx_employees_empresa_cpf', 'company_id', 'cpf'),
        Index('idx_employees_empresa_matricula', 'company_id', 'matricula'),
    )
    company_id: Mapped[int | None] = mapped_column(ForeignKey('companies.id', ondelete='RESTRICT'), index=True)
    nome: Mapped[str | None] = mapped_column(Text)
    cpf: Mapped[str | None] = mapped_column(Text)
    matricula: Mapped[str | None] = mapped_column(Text)
    cargo: Mapped[str | None] = mapped_column(Text)
    centro_custo: Mapped[str | None] = mapped_column(Text)
    codigo_correntista: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text, server_default='Ativo')
    name = synonym('nome')
    registration = synonym('matricula')
    company: Mapped[Company | None] = relationship(back_populates='employees')
