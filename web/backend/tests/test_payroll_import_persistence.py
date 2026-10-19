import os
from datetime import timezone
from sqlalchemy import Integer, String
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

import pytest

from app.models import AuditLog, Company, PayrollImport, PayrollLine, Role, User, UserCompany
from app.services.payroll_import import persist_import


@pytest.fixture
def import_db():
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to a disposable, migrated PostgreSQL')
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode='create_savepoint') as db:
            role = db.scalar(select(Role).where(Role.name == 'Operador'))
            if role is None:
                role = Role(name='Operador')
                db.add(role)
            company = Company(razao='Empresa sintética', cnpj='11222333000181', status='Ativa')
            db.add(company)
            db.flush()
            actor = User(email='import@example.test', password_hash='test', role_id=role.id)
            db.add(actor)
            db.flush()
            db.add(UserCompany(user_id=actor.id, company_id=company.id))
            actor_id, company_id = actor.id, company.id
            db.commit()
            yield db, actor_id, company_id
        transaction.rollback()
    engine.dispose()


def statement():
    return {
        'competencia': '10/2026',
        'empresa': {'codigo_siagri': '1', 'razao': 'Empresa sintética', 'cnpj': '11222333000181'},
        'tipo_importacao': 'Extrato',
        'colaboradores': [{
            'matricula': '1', 'nome': 'Ana Sintética', 'cpf': '00000000000', 'situacao': 'Ativo',
            'cargo': 'Analista', 'centro_custo': '01', 'liquido': Decimal('123.4567'),
            'rubricas': [
                {'codigo': '001', 'descricao': 'Salário', 'referencia': '30', 'valor': Decimal('100.1234567'), 'tipo': 'P'},
                {'codigo': '001', 'descricao': 'Salário duplicado', 'referencia': '1', 'valor': Decimal('0.0000001'), 'tipo': 'P'},
            ],
        }],
    }


def test_import_metadata_columns_are_nullable_and_preserve_legacy_fields():
    columns = PayrollImport.__table__.c

    assert isinstance(columns.arquivo_sha256.type, String)
    assert columns.arquivo_sha256.type.length == 64
    assert columns.arquivo_sha256.nullable
    for name in ('arquivo_bytes', 'quantidade_colaboradores', 'quantidade_rubricas'):
        assert isinstance(columns[name].type, Integer)
        assert columns[name].nullable

    assert columns.arquivo.nullable
    assert columns.data_hora.nullable
    assert columns.status.nullable
    assert columns.stored_file_id.nullable


def test_persist_import_preserves_lines_and_stages_metadata_audit(import_db):
    db, actor_id, company_id = import_db
    result = persist_import(
        db, actor_id=actor_id, company_id=company_id, competence='10/2026',
        filename='folha.xlsx', size_bytes=123, sha256='a' * 64, statement=statement(),
    )

    assert result.competencia == '10/2026'
    assert result.arquivo == 'folha.xlsx'
    assert result.arquivo_sha256 == 'a' * 64
    assert result.arquivo_bytes == 123
    assert result.quantidade_colaboradores == 1
    assert result.quantidade_rubricas == 2
    assert result.stored_file_id is None
    timestamp = datetime.fromisoformat(result.data_hora.replace('Z', '+00:00'))
    assert timestamp.tzinfo is not None and timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)

    lines = db.scalars(select(PayrollLine).where(PayrollLine.import_id == result.id).order_by(PayrollLine.id)).all()
    assert [(line.codigo_verba, line.verba, line.valor, line.liquido) for line in lines] == [
        ('001', 'Salário', Decimal('100.1234567'), Decimal('123.4567')),
        ('001', 'Salário duplicado', Decimal('0.0000001'), Decimal('123.4567')),
    ]
    audits = db.scalars(select(AuditLog).where(AuditLog.entity_id == result.id)).all()
    assert len(audits) == 1
    assert audits[0].actor_id == actor_id
    assert audits[0].company_id == company_id
    assert audits[0].created_at.isoformat() == timestamp.isoformat()
    assert audits[0].details == {'sha256': 'a' * 64, 'employees': 1, 'rubrics': 2}
    assert 'Ana Sintética' not in str(audits[0].details)
    assert '00000000000' not in str(audits[0].details)


def test_persist_import_rolls_back_import_lines_when_audit_fails(import_db, monkeypatch):
    import app.services.payroll_import as service

    db, actor_id, company_id = import_db

    def fail_audit(*args, **kwargs):
        raise RuntimeError('injected audit failure')

    monkeypatch.setattr(service, 'write_audit', fail_audit)
    with pytest.raises(RuntimeError, match='injected audit failure'):
        service.persist_import(
            db, actor_id=actor_id, company_id=company_id, competence='10/2026',
            filename='folha.xlsx', size_bytes=123, sha256='a' * 64, statement=statement(),
        )
    assert db.scalar(select(func.count()).select_from(PayrollImport)) == 0
    assert db.scalar(select(func.count()).select_from(PayrollLine)) == 0
    assert db.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_persist_import_rolls_back_all_rows_when_line_flush_fails(import_db):
    db, actor_id, company_id = import_db

    def fail_before_flush(session, flush_context, instances):
        if any(isinstance(item, PayrollLine) for item in session.new):
            raise RuntimeError('injected line failure')

    event.listen(db, 'before_flush', fail_before_flush)
    try:
        with pytest.raises(RuntimeError, match='injected line failure'):
            persist_import(
                db, actor_id=actor_id, company_id=company_id, competence='10/2026',
                filename='folha.xlsx', size_bytes=123, sha256='a' * 64, statement=statement(),
            )
    finally:
        event.remove(db, 'before_flush', fail_before_flush)
    assert db.scalar(select(func.count()).select_from(PayrollImport)) == 0
    assert db.scalar(select(func.count()).select_from(PayrollLine)) == 0
    assert db.scalar(select(func.count()).select_from(AuditLog)) == 0
