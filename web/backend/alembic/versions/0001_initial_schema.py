"""Initial web schema preserving legacy integer IDs and operational columns.

Revision ID: 0001
Revises: (base)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('companies',
    sa.Column('codigo_siagri', sa.Text(), nullable=True),
    sa.Column('razao', sa.Text(), nullable=True),
    sa.Column('fantasia', sa.Text(), nullable=True),
    sa.Column('cnpj', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default='Ativa', nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_companies'))
    )
    op.create_table('roles',
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
    sa.UniqueConstraint('name', name=op.f('uq_roles_name'))
    )
    op.create_table('chart_accounts',
    sa.Column('conta', sa.Text(), nullable=True),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('utiliza_cc', sa.Integer(), server_default=sa.text('0'), nullable=True),
    sa.Column('tipo_correntista', sa.Text(), server_default='9-Nenhum', nullable=True),
    sa.Column('gera_cor', sa.Integer(), server_default=sa.text('0'), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_chart_accounts_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_chart_accounts'))
    )
    op.create_index(op.f('ix_chart_accounts_company_id'), 'chart_accounts', ['company_id'], unique=False)
    op.create_table('employees',
    sa.Column('company_id', sa.BigInteger(), nullable=True),
    sa.Column('nome', sa.Text(), nullable=True),
    sa.Column('cpf', sa.Text(), nullable=True),
    sa.Column('matricula', sa.Text(), nullable=True),
    sa.Column('cargo', sa.Text(), nullable=True),
    sa.Column('centro_custo', sa.Text(), nullable=True),
    sa.Column('codigo_correntista', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default='Ativo', nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_employees_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_employees'))
    )
    op.create_index('idx_employees_empresa_cpf', 'employees', ['company_id', 'cpf'], unique=False)
    op.create_index('idx_employees_empresa_matricula', 'employees', ['company_id', 'matricula'], unique=False)
    op.create_index(op.f('ix_employees_company_id'), 'employees', ['company_id'], unique=False)
    op.create_table('finance_params',
    sa.Column('tipo', sa.Text(), nullable=True),
    sa.Column('documento_id', sa.Text(), nullable=True),
    sa.Column('parceiro_cpf_cnpj', sa.Text(), nullable=True),
    sa.Column('codigo_parceiro_siagri', sa.Text(), nullable=True),
    sa.Column('conta_contrapartida', sa.Text(), nullable=True),
    sa.Column('centro_custo', sa.Text(), nullable=True),
    sa.Column('vencimento_dia', sa.Integer(), nullable=True),
    sa.Column('historico', sa.Text(), nullable=True),
    sa.Column('ativo', sa.Integer(), server_default=sa.text('1'), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_finance_params_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_finance_params'))
    )
    op.create_index(op.f('ix_finance_params_company_id'), 'finance_params', ['company_id'], unique=False)
    op.create_table('rubrics',
    sa.Column('codigo', sa.Text(), nullable=True),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('tipo', sa.Text(), nullable=True),
    sa.Column('conta_debito', sa.Text(), nullable=True),
    sa.Column('conta_credito', sa.Text(), nullable=True),
    sa.Column('historico_id', sa.Text(), nullable=True),
    sa.Column('historico', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default='Ativa', nullable=True),
    sa.Column('debito_gera_cc', sa.Integer(), server_default=sa.text('1'), nullable=True),
    sa.Column('debito_gera_cor', sa.Integer(), server_default=sa.text('1'), nullable=True),
    sa.Column('credito_gera_cc', sa.Integer(), server_default=sa.text('1'), nullable=True),
    sa.Column('credito_gera_cor', sa.Integer(), server_default=sa.text('1'), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_rubrics_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rubrics'))
    )
    op.create_index(op.f('ix_rubrics_company_id'), 'rubrics', ['company_id'], unique=False)
    op.create_table('stored_files',
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('original_name', sa.String(length=255), nullable=False),
    sa.Column('storage_key', sa.String(length=512), nullable=False),
    sa.Column('content_type', sa.String(length=255), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
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
    sa.Column('role_id', sa.BigInteger(), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_users_role_id_roles'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_index(op.f('ix_users_role_id'), 'users', ['role_id'], unique=False)
    op.create_table('audit_logs',
    sa.Column('actor_id', sa.BigInteger(), nullable=True),
    sa.Column('company_id', sa.BigInteger(), nullable=True),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('entity', sa.String(length=80), nullable=False),
    sa.Column('entity_id', sa.BigInteger(), nullable=True),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_audit_logs_actor_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_audit_logs_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_index('ix_audit_logs_company_created', 'audit_logs', ['company_id', 'created_at'], unique=False)
    op.create_table('imports',
    sa.Column('competencia', sa.Text(), nullable=True),
    sa.Column('arquivo', sa.Text(), nullable=True),
    sa.Column('data_hora', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), nullable=True),
    sa.Column('stored_file_id', sa.BigInteger(), nullable=True),
    sa.Column('created_by_id', sa.BigInteger(), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'stored_file_id'], ['stored_files.company_id', 'stored_files.id'], name=op.f('fk_imports_company_id_stored_file_id_stored_files'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_imports_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_imports_created_by_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['stored_file_id'], ['stored_files.id'], name=op.f('fk_imports_stored_file_id_stored_files'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_imports')),
    sa.UniqueConstraint('company_id', 'id', name=op.f('uq_imports_company_id_id'))
    )
    op.create_index('idx_imports_empresa_comp', 'imports', ['company_id', 'competencia', 'status'], unique=False)
    op.create_index(op.f('ix_imports_company_id'), 'imports', ['company_id'], unique=False)
    op.create_table('refresh_tokens',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('family_id', sa.Uuid(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
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
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_user_companies_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_companies_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_companies')),
    sa.UniqueConstraint('user_id', 'company_id', name=op.f('uq_user_companies_user_id_company_id'))
    )
    op.create_index(op.f('ix_user_companies_company_id'), 'user_companies', ['company_id'], unique=False)
    op.create_table('payroll_lines',
    sa.Column('import_id', sa.BigInteger(), nullable=True),
    sa.Column('cpf', sa.Text(), nullable=True),
    sa.Column('nome', sa.Text(), nullable=True),
    sa.Column('cargo', sa.Text(), nullable=True),
    sa.Column('codigo_verba', sa.Text(), nullable=True),
    sa.Column('verba', sa.Text(), nullable=True),
    sa.Column('referencia', sa.Text(), nullable=True),
    sa.Column('valor', sa.Numeric(), nullable=True),
    sa.Column('tipo', sa.Text(), nullable=True),
    sa.Column('liquido', sa.Numeric(), server_default=sa.text('0'), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'import_id'], ['imports.company_id', 'imports.id'], name=op.f('fk_payroll_lines_company_id_import_id_imports'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_payroll_lines_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['import_id'], ['imports.id'], name=op.f('fk_payroll_lines_import_id_imports'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payroll_lines'))
    )
    op.create_index('idx_payroll_empresa_import', 'payroll_lines', ['company_id', 'import_id'], unique=False)
    op.create_index(op.f('ix_payroll_lines_company_id'), 'payroll_lines', ['company_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_payroll_lines_company_id'), table_name='payroll_lines')
    op.drop_index('idx_payroll_empresa_import', table_name='payroll_lines')
    op.drop_table('payroll_lines')
    op.drop_index(op.f('ix_user_companies_company_id'), table_name='user_companies')
    op.drop_table('user_companies')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_family_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_expires_at'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index(op.f('ix_imports_company_id'), table_name='imports')
    op.drop_index('idx_imports_empresa_comp', table_name='imports')
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
    op.drop_index('idx_employees_empresa_matricula', table_name='employees')
    op.drop_index('idx_employees_empresa_cpf', table_name='employees')
    op.drop_table('employees')
    op.drop_index(op.f('ix_chart_accounts_company_id'), table_name='chart_accounts')
    op.drop_table('chart_accounts')
    op.drop_table('roles')
    op.drop_table('companies')
