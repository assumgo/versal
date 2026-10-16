"""initial_schema

Revision ID: 0001
Revises: (base)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('companies',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('cnpj', sa.String(length=14), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_companies')),
    sa.UniqueConstraint('cnpj', name=op.f('uq_companies_cnpj'))
    )
    op.create_table('roles',
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
    sa.UniqueConstraint('name', name=op.f('uq_roles_name'))
    )
    op.create_table('chart_accounts',
    sa.Column('code', sa.String(length=60), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_chart_accounts_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_chart_accounts')),
    sa.UniqueConstraint('company_id', 'code', name=op.f('uq_chart_accounts_company_id_code'))
    )
    op.create_index(op.f('ix_chart_accounts_company_id'), 'chart_accounts', ['company_id'], unique=False)
    op.create_table('employees',
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.Column('registration', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('cpf', sa.String(length=11), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_employees_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_employees')),
    sa.UniqueConstraint('company_id', 'cpf', name=op.f('uq_employees_company_id_cpf')),
    sa.UniqueConstraint('company_id', 'id', name=op.f('uq_employees_company_id_id')),
    sa.UniqueConstraint('company_id', 'registration', name=op.f('uq_employees_company_id_registration'))
    )
    op.create_index(op.f('ix_employees_company_id'), 'employees', ['company_id'], unique=False)
    op.create_table('finance_params',
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_finance_params_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_finance_params')),
    sa.UniqueConstraint('company_id', 'key', name=op.f('uq_finance_params_company_id_key'))
    )
    op.create_index(op.f('ix_finance_params_company_id'), 'finance_params', ['company_id'], unique=False)
    op.create_table('rubrics',
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_rubrics_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rubrics')),
    sa.UniqueConstraint('company_id', 'code', name=op.f('uq_rubrics_company_id_code')),
    sa.UniqueConstraint('company_id', 'id', name=op.f('uq_rubrics_company_id_id'))
    )
    op.create_index(op.f('ix_rubrics_company_id'), 'rubrics', ['company_id'], unique=False)
    op.create_table('stored_files',
    sa.Column('original_name', sa.String(length=255), nullable=False),
    sa.Column('storage_key', sa.String(length=512), nullable=False),
    sa.Column('content_type', sa.String(length=255), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('size_bytes >= 0', name=op.f('ck_stored_files_nonnegative_size')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_stored_files_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stored_files')),
    sa.UniqueConstraint('company_id', 'id', name=op.f('uq_stored_files_company_id_id')),
    sa.UniqueConstraint('storage_key', name=op.f('uq_stored_files_storage_key'))
    )
    op.create_index(op.f('ix_stored_files_company_id'), 'stored_files', ['company_id'], unique=False)
    op.create_table('users',
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role_id', sa.Uuid(), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_users_role_id_roles'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_index(op.f('ix_users_role_id'), 'users', ['role_id'], unique=False)
    op.create_table('audit_logs',
    sa.Column('actor_id', sa.Uuid(), nullable=True),
    sa.Column('company_id', sa.Uuid(), nullable=True),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('entity', sa.String(length=80), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=True),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_audit_logs_actor_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_audit_logs_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_index('ix_audit_logs_company_created', 'audit_logs', ['company_id', 'created_at'], unique=False)
    op.create_table('imports',
    sa.Column('competence', sa.Date(), nullable=False),
    sa.Column('stored_file_id', sa.Uuid(), nullable=True),
    sa.Column('created_by_id', sa.Uuid(), nullable=True),
    sa.Column('status', sa.String(length=30), server_default='pending', nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('EXTRACT(DAY FROM competence) = 1', name=op.f('ck_imports_competence_month')),
    sa.ForeignKeyConstraint(['company_id', 'stored_file_id'], ['stored_files.company_id', 'stored_files.id'], name=op.f('fk_imports_company_id_stored_file_id_stored_files'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_imports_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_imports_created_by_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_imports')),
    sa.UniqueConstraint('company_id', 'id', name=op.f('uq_imports_company_id_id'))
    )
    op.create_index('ix_imports_company_competence', 'imports', ['company_id', 'competence'], unique=False)
    op.create_index(op.f('ix_imports_company_id'), 'imports', ['company_id'], unique=False)
    op.create_table('refresh_tokens',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('family_id', sa.Uuid(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_refresh_tokens_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_refresh_tokens_token_hash'))
    )
    op.create_index(op.f('ix_refresh_tokens_expires_at'), 'refresh_tokens', ['expires_at'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_family_id'), 'refresh_tokens', ['family_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_table('user_companies',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_user_companies_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_companies_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_companies')),
    sa.UniqueConstraint('user_id', 'company_id', name=op.f('uq_user_companies_user_id_company_id'))
    )
    op.create_index(op.f('ix_user_companies_company_id'), 'user_companies', ['company_id'], unique=False)
    op.create_table('payroll_lines',
    sa.Column('competence', sa.Date(), nullable=False),
    sa.Column('employee_id', sa.Uuid(), nullable=True),
    sa.Column('rubric_id', sa.Uuid(), nullable=True),
    sa.Column('import_id', sa.Uuid(), nullable=True),
    sa.Column('value', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('EXTRACT(DAY FROM competence) = 1', name=op.f('ck_payroll_lines_competence_month')),
    sa.ForeignKeyConstraint(['company_id', 'employee_id'], ['employees.company_id', 'employees.id'], name=op.f('fk_payroll_lines_company_id_employee_id_employees'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id', 'import_id'], ['imports.company_id', 'imports.id'], name=op.f('fk_payroll_lines_company_id_import_id_imports'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id', 'rubric_id'], ['rubrics.company_id', 'rubrics.id'], name=op.f('fk_payroll_lines_company_id_rubric_id_rubrics'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_payroll_lines_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payroll_lines'))
    )
    op.create_index('ix_payroll_lines_company_competence', 'payroll_lines', ['company_id', 'competence'], unique=False)
    op.create_index(op.f('ix_payroll_lines_company_id'), 'payroll_lines', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payroll_lines_company_id'), table_name='payroll_lines')
    op.drop_index('ix_payroll_lines_company_competence', table_name='payroll_lines')
    op.drop_table('payroll_lines')
    op.drop_index(op.f('ix_user_companies_company_id'), table_name='user_companies')
    op.drop_table('user_companies')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_family_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_expires_at'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index(op.f('ix_imports_company_id'), table_name='imports')
    op.drop_index('ix_imports_company_competence', table_name='imports')
    op.drop_table('imports')
    op.drop_index('ix_audit_logs_company_created', table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_users_role_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_stored_files_company_id'), table_name='stored_files')
    op.drop_table('stored_files')
    op.drop_index(op.f('ix_rubrics_company_id'), table_name='rubrics')
    op.drop_table('rubrics')
    op.drop_index(op.f('ix_finance_params_company_id'), table_name='finance_params')
    op.drop_table('finance_params')
    op.drop_index(op.f('ix_employees_company_id'), table_name='employees')
    op.drop_table('employees')
    op.drop_index(op.f('ix_chart_accounts_company_id'), table_name='chart_accounts')
    op.drop_table('chart_accounts')
    op.drop_table('roles')
    op.drop_table('companies')
