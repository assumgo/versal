from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdentityMixin, TimestampMixin


class CompanyScope:
    company_id: Mapped[UUID] = mapped_column(ForeignKey('companies.id', ondelete='RESTRICT'), index=True)


class Rubric(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'rubrics'
    __table_args__ = (UniqueConstraint('company_id', 'code'), UniqueConstraint('company_id', 'id'))
    code: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(String(255))


class ChartAccount(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'chart_accounts'
    __table_args__ = (UniqueConstraint('company_id', 'code'),)
    code: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(String(255))


class FinanceParam(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'finance_params'
    __table_args__ = (UniqueConstraint('company_id', 'key'),)
    key: Mapped[str] = mapped_column(String(100))
    value: Mapped[dict] = mapped_column(JSONB)


class StoredFile(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'stored_files'
    __table_args__ = (UniqueConstraint('company_id', 'id'), CheckConstraint('size_bytes >= 0', name='nonnegative_size'))
    original_name: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    content_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))


class PayrollImport(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'imports'
    __table_args__ = (
        UniqueConstraint('company_id', 'id'),
        ForeignKeyConstraint(['company_id', 'stored_file_id'], ['stored_files.company_id', 'stored_files.id'], ondelete='RESTRICT'),
        CheckConstraint('EXTRACT(DAY FROM competence) = 1', name='competence_month'),
        Index('ix_imports_company_competence', 'company_id', 'competence'),
    )
    competence: Mapped[date] = mapped_column(Date)
    stored_file_id: Mapped[UUID | None]
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'))
    status: Mapped[str] = mapped_column(String(30), server_default='pending')


class PayrollLine(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'payroll_lines'
    __table_args__ = (
        ForeignKeyConstraint(['company_id', 'employee_id'], ['employees.company_id', 'employees.id'], ondelete='RESTRICT'),
        ForeignKeyConstraint(['company_id', 'rubric_id'], ['rubrics.company_id', 'rubrics.id'], ondelete='RESTRICT'),
        ForeignKeyConstraint(['company_id', 'import_id'], ['imports.company_id', 'imports.id'], ondelete='RESTRICT'),
        CheckConstraint('EXTRACT(DAY FROM competence) = 1', name='competence_month'),
        Index('ix_payroll_lines_company_competence', 'company_id', 'competence'),
    )
    competence: Mapped[date] = mapped_column(Date)
    employee_id: Mapped[UUID | None]
    rubric_id: Mapped[UUID | None]
    import_id: Mapped[UUID | None]
    value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
