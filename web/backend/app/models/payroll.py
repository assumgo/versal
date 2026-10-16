from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, synonym

from app.models.base import Base, IdentityMixin, TimestampMixin


class CompanyScope:
    # Legacy tables allow NULL; orphan IDs must be audited before a real migration.
    company_id: Mapped[int | None] = mapped_column(ForeignKey('companies.id', ondelete='RESTRICT'), index=True)


class Rubric(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'rubrics'
    codigo: Mapped[str | None] = mapped_column(Text)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str | None] = mapped_column(Text)
    conta_debito: Mapped[str | None] = mapped_column(Text)
    conta_credito: Mapped[str | None] = mapped_column(Text)
    historico_id: Mapped[str | None] = mapped_column(Text)
    historico: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text, server_default='Ativa')
    debito_gera_cc: Mapped[int | None] = mapped_column(Integer, server_default=text('1'))
    debito_gera_cor: Mapped[int | None] = mapped_column(Integer, server_default=text('1'))
    credito_gera_cc: Mapped[int | None] = mapped_column(Integer, server_default=text('1'))
    credito_gera_cor: Mapped[int | None] = mapped_column(Integer, server_default=text('1'))
    code = synonym('codigo')
    description = synonym('descricao')


class ChartAccount(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'chart_accounts'
    conta: Mapped[str | None] = mapped_column(Text)
    descricao: Mapped[str | None] = mapped_column(Text)
    utiliza_cc: Mapped[int | None] = mapped_column(Integer, server_default=text('0'))
    tipo_correntista: Mapped[str | None] = mapped_column(Text, server_default='9-Nenhum')
    gera_cor: Mapped[int | None] = mapped_column(Integer, server_default=text('0'))
    code = synonym('conta')
    description = synonym('descricao')


class FinanceParam(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'finance_params'
    tipo: Mapped[str | None] = mapped_column(Text)
    documento_id: Mapped[str | None] = mapped_column(Text)
    parceiro_cpf_cnpj: Mapped[str | None] = mapped_column(Text)
    codigo_parceiro_siagri: Mapped[str | None] = mapped_column(Text)
    conta_contrapartida: Mapped[str | None] = mapped_column(Text)
    centro_custo: Mapped[str | None] = mapped_column(Text)
    vencimento_dia: Mapped[int | None] = mapped_column(Integer)
    historico: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[int | None] = mapped_column(Integer, server_default=text('1'))


class StoredFile(IdentityMixin, TimestampMixin, Base):
    __tablename__ = 'stored_files'
    __table_args__ = (UniqueConstraint('company_id', 'id'), CheckConstraint('size_bytes >= 0', name='nonnegative_size'))
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id', ondelete='RESTRICT'), index=True)
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
        Index('idx_imports_empresa_comp', 'company_id', 'competencia', 'status'),
    )
    competencia: Mapped[str | None] = mapped_column(Text)
    arquivo: Mapped[str | None] = mapped_column(Text)
    data_hora: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    stored_file_id: Mapped[int | None] = mapped_column(ForeignKey('stored_files.id', ondelete='RESTRICT'))
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'))
    competence = synonym('competencia')


class PayrollLine(IdentityMixin, TimestampMixin, CompanyScope, Base):
    __tablename__ = 'payroll_lines'
    __table_args__ = (
        ForeignKeyConstraint(['company_id', 'import_id'], ['imports.company_id', 'imports.id'], ondelete='RESTRICT'),
        Index('idx_payroll_empresa_import', 'company_id', 'import_id'),
    )
    import_id: Mapped[int | None] = mapped_column(ForeignKey('imports.id', ondelete='RESTRICT'))
    cpf: Mapped[str | None] = mapped_column(Text)
    nome: Mapped[str | None] = mapped_column(Text)
    cargo: Mapped[str | None] = mapped_column(Text)
    codigo_verba: Mapped[str | None] = mapped_column(Text)
    verba: Mapped[str | None] = mapped_column(Text)
    referencia: Mapped[str | None] = mapped_column(Text)
    valor: Mapped[Decimal | None] = mapped_column(Numeric())
    tipo: Mapped[str | None] = mapped_column(Text)
    liquido: Mapped[Decimal | None] = mapped_column(Numeric(), server_default=text('0'))
    value = synonym('valor')
