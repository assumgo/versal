import os
from decimal import Decimal

import pytest
from sqlalchemy import Numeric, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Company, Employee, PayrollLine, Role, User, UserCompany


def test_initial_schema_has_all_tables():
    assert set(Base.metadata.tables) == {
        'roles', 'users', 'user_companies', 'companies', 'employees', 'rubrics',
        'chart_accounts', 'finance_params', 'imports', 'payroll_lines',
        'stored_files', 'audit_logs', 'refresh_tokens',
    }


@pytest.mark.parametrize('field', ['valor', 'liquido'])
def test_payroll_money_preserves_legacy_numeric_scale(field):
    column = PayrollLine.__table__.c[field]
    assert isinstance(column.type, Numeric)
    assert column.type.precision is None
    assert column.type.scale is None
    assert column.type.asdecimal


@pytest.fixture
def db():
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to a disposable, migrated PostgreSQL')
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode='create_savepoint') as session:
            yield session
        transaction.rollback()
    engine.dispose()


def identity(db):
    role = Role(name='Operador')
    company = Company(name='Empresa teste', cnpj='11222333000181')
    db.add_all([role, company])
    db.flush()
    user = User(email='user@example.test', password_hash='argon2-test-placeholder', role_id=role.id)
    db.add(user)
    db.flush()
    return user, company


@pytest.mark.parametrize('entity', ['role', 'email', 'membership'])
def test_duplicate_identity_is_rejected(db, entity):
    user, company = identity(db)
    if entity == 'role':
        duplicate = Role(name='Operador')
    elif entity == 'email':
        duplicate = User(email=user.email, password_hash='other', role_id=user.role_id)
    else:
        db.add(UserCompany(user_id=user.id, company_id=company.id))
        db.flush()
        duplicate = UserCompany(user_id=user.id, company_id=company.id)
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.flush()


def test_employee_requires_existing_company(db):
    db.add(Employee(company_id=999999999, name='Sem empresa', registration='1', cpf='12345678909'))
    with pytest.raises(IntegrityError):
        db.flush()


def test_company_with_employee_cannot_be_deleted(db):
    _, company = identity(db)
    db.add(Employee(company_id=company.id, name='Pessoa', registration='1', cpf='12345678909'))
    db.flush()
    with pytest.raises(IntegrityError):
        db.execute(text('DELETE FROM companies WHERE id = :id'), {'id': company.id})


def test_migration_contains_all_model_tables(db):
    assert set(Base.metadata.tables) <= set(inspect(db.connection()).get_table_names())


@pytest.mark.parametrize('amount', ['1234567890123.45', '0.12345', '123456789012345678901.1234567'])
def test_money_round_trip_and_utc_timestamp(db, amount):
    _, company = identity(db)
    line = PayrollLine(company_id=company.id, value=Decimal(amount), liquido=Decimal(amount))
    db.add(line)
    db.flush()
    db.refresh(line)
    assert line.value == Decimal(amount)
    assert line.liquido == Decimal(amount)
    assert line.created_at.utcoffset().total_seconds() == 0


@pytest.mark.parametrize('reference', ['import', 'file'])
def test_operational_references_cannot_cross_companies(db, reference):
    from app.models import PayrollImport, StoredFile

    _, company = identity(db)
    other = Company(name='Outra', cnpj='11222333000262')
    db.add(other)
    db.flush()
    if reference == 'import':
        target = PayrollImport(company_id=other.id, competence='10/2026')
    else:
        target = StoredFile(company_id=other.id, original_name='folha.txt', storage_key='test/key',
                            content_type='text/plain', size_bytes=1, sha256='a' * 64)
    db.add(target)
    db.flush()
    if reference == 'file':
        record = PayrollImport(company_id=company.id, stored_file_id=target.id, competence='10/2026')
    else:
        record = PayrollLine(company_id=company.id, import_id=target.id, value=Decimal('10.00'))
    db.add(record)
    with pytest.raises(IntegrityError):
        db.flush()


def test_get_db_rolls_back_uncommitted_changes(monkeypatch, db):
    from app.core.config import get_settings
    from app.core.database import get_db, get_engine

    monkeypatch.setenv('DATABASE_URL', os.environ['TEST_DATABASE_URL'])
    get_settings.cache_clear()
    get_engine.cache_clear()
    dependency = get_db()
    try:
        session = next(dependency)
        session.add(Role(name='Uncommitted role'))
        session.flush()
        dependency.close()
        assert db.execute(text("SELECT count(*) FROM roles WHERE name = 'Uncommitted role'")).scalar_one() == 0
    finally:
        dependency.close()
        get_engine().dispose()
        get_engine.cache_clear()
        get_settings.cache_clear()


@pytest.fixture
def legacy():
    import sqlite3
    from pathlib import Path

    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    connection.executescript(Path(__file__).with_name('fixtures').joinpath('legacy_schema.sql').read_text())
    yield connection
    connection.close()


@pytest.mark.parametrize('table_name', ['companies', 'employees', 'rubrics', 'chart_accounts',
                                       'finance_params', 'imports', 'payroll_lines'])
def test_legacy_columns_and_integer_ids_are_preserved(legacy, table_name):
    from sqlalchemy import BigInteger, Integer

    columns = legacy.execute(f'PRAGMA table_info({table_name})').fetchall()
    target = Base.metadata.tables[table_name]
    assert {column['name'] for column in columns} <= set(target.c.keys())
    assert isinstance(target.c.id.type, (Integer, BigInteger))
    assert target.c.id.identity is not None
    assert not target.c.id.identity.always  # Existing integer IDs can be inserted explicitly.
    for column in columns:
        if column['name'] != 'id':
            assert target.c[column['name']].nullable


def test_legacy_rows_keep_ids_relationships_and_fields(db, legacy):
    rows = {
        'companies': {'id': 41, 'codigo_siagri': '008', 'razao': 'Empresa sintética', 'fantasia': 'Teste', 'cnpj': '11.222.333/0001-81', 'status': 'Ativa'},
        'employees': {'id': 73, 'company_id': 41, 'nome': 'Pessoa sintética', 'cpf': '123.456.789-09', 'matricula': '0007', 'cargo': 'Auxiliar', 'centro_custo': '01', 'codigo_correntista': '009', 'status': 'Ativo'},
        'rubrics': {'id': 89, 'company_id': 41, 'codigo': '001', 'descricao': 'Salário', 'tipo': 'Provento', 'conta_debito': '4.1', 'conta_credito': '2.1', 'historico_id': '1000182', 'historico': 'Folha', 'status': 'Ativa', 'debito_gera_cc': 1, 'debito_gera_cor': 0, 'credito_gera_cc': 1, 'credito_gera_cor': 0},
        'chart_accounts': {'id': 101, 'company_id': 41, 'conta': '4.1', 'descricao': 'Salários', 'utiliza_cc': 1, 'tipo_correntista': '9-Nenhum', 'gera_cor': 0},
        'finance_params': {'id': 131, 'company_id': 41, 'tipo': 'Salário', 'documento_id': '007', 'parceiro_cpf_cnpj': '11.222.333/0001-81', 'codigo_parceiro_siagri': '008', 'conta_contrapartida': '2.1', 'centro_custo': '01', 'vencimento_dia': 5, 'historico': 'Pagamento', 'ativo': 1},
        'imports': {'id': 157, 'company_id': 41, 'competencia': '10/2026', 'arquivo': 'folha.xlsx', 'data_hora': '2026-10-16 09:00:00', 'status': 'Concluída'},
        'payroll_lines': {'id': 211, 'import_id': 157, 'company_id': 41, 'cpf': '123.456.789-09', 'nome': 'Pessoa sintética', 'cargo': 'Auxiliar', 'codigo_verba': '001', 'verba': 'Salário', 'referencia': '30', 'valor': 1234.56, 'tipo': 'Provento', 'liquido': 1100.25},
    }
    for table_name, values in rows.items():
        columns = ', '.join(values)
        placeholders = ', '.join('?' for _ in values)
        legacy.execute(f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})', tuple(values.values()))
        source = dict(legacy.execute(f'SELECT * FROM {table_name} WHERE id = ?', (values['id'],)).fetchone())
        table = Base.metadata.tables[table_name]
        db.execute(table.insert().values(**source))
        result = db.execute(table.select().where(table.c.id == source['id'])).mappings().one()
        for key, value in source.items():
            expected = Decimal(str(value)) if key in {'valor', 'liquido'} and value is not None else value
            assert result[key] == expected, (table_name, key)
    assert db.execute(text('SELECT p.id, p.company_id, p.import_id FROM payroll_lines p JOIN imports i ON i.id=p.import_id JOIN companies c ON c.id=i.company_id WHERE p.id=211')).one() == (211, 41, 157)


def test_legacy_nullable_and_duplicate_employee_fields_are_accepted(db):
    _, company = identity(db)
    db.add_all([Employee(company_id=company.id, name=None, registration=None, cpf=None),
                Employee(company_id=company.id, name='Pessoa', registration='001', cpf='123.456.789-09'),
                Employee(company_id=company.id, name='Pessoa', registration='001', cpf='123.456.789-09')])
    db.flush()


def test_identity_sequence_can_continue_after_preserved_legacy_id(db):
    db.add(Company(id=9876543210, name='ID legado alto', cnpj=None))
    db.flush()
    db.execute(text("SELECT setval(pg_get_serial_sequence('companies', 'id'), (SELECT MAX(id) FROM companies), true)"))
    company = Company(name='Nova empresa')
    db.add(company)
    db.flush()
    assert company.id == 9876543211
