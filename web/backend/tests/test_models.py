import os
from datetime import date
from decimal import Decimal
from uuid import uuid4

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


def test_payroll_money_is_fixed_precision():
    column = PayrollLine.__table__.c.value
    assert isinstance(column.type, Numeric)
    assert (column.type.precision, column.type.scale) == (18, 2)
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
    db.add(Employee(company_id=uuid4(), name='Sem empresa', registration='1', cpf='12345678909'))
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


def test_money_round_trip_and_utc_timestamp(db):
    _, company = identity(db)
    line = PayrollLine(company_id=company.id, competence=date(2026, 10, 1), value=Decimal('1234567890123.45'))
    db.add(line)
    db.flush()
    db.refresh(line)
    assert line.value == Decimal('1234567890123.45')
    assert line.created_at.utcoffset().total_seconds() == 0


def test_payroll_rejects_employee_from_another_company(db):
    _, company = identity(db)
    other = Company(name='Outra', cnpj='11222333000262')
    db.add(other)
    db.flush()
    employee = Employee(company_id=other.id, name='Pessoa', registration='1', cpf='12345678909')
    db.add(employee)
    db.flush()
    db.add(PayrollLine(company_id=company.id, employee_id=employee.id, competence=date(2026, 10, 1), value=Decimal('10.00')))
    with pytest.raises(IntegrityError):
        db.flush()


def test_competence_requires_first_day(db):
    _, company = identity(db)
    db.add(PayrollLine(company_id=company.id, competence=date(2026, 10, 16), value=Decimal('10.00')))
    with pytest.raises(IntegrityError):
        db.flush()


@pytest.mark.parametrize('reference', ['rubric', 'import', 'file'])
def test_operational_references_cannot_cross_companies(db, reference):
    from app.models import PayrollImport, Rubric, StoredFile

    _, company = identity(db)
    other = Company(name='Outra', cnpj='11222333000262')
    db.add(other)
    db.flush()
    if reference == 'rubric':
        target = Rubric(company_id=other.id, code='1', description='Salário')
    elif reference == 'import':
        target = PayrollImport(company_id=other.id, competence=date(2026, 10, 1))
    else:
        target = StoredFile(company_id=other.id, original_name='folha.txt', storage_key='test/key',
                            content_type='text/plain', size_bytes=1, sha256='a' * 64)
    db.add(target)
    db.flush()
    if reference == 'file':
        record = PayrollImport(company_id=company.id, stored_file_id=target.id, competence=date(2026, 10, 1))
    else:
        kwargs = {'rubric_id' if reference == 'rubric' else 'import_id': target.id}
        record = PayrollLine(company_id=company.id, competence=date(2026, 10, 1), value=Decimal('10.00'), **kwargs)
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
