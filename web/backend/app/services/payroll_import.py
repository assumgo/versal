"""Atomic persistence for a parsed, ready payroll statement."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Company, PayrollImport, PayrollLine, User
from app.parsers.types import ParsedStatement
from app.services.audit import write_audit
from app.services.authorization import require_company_access

IMPORT_ROLES = {'Administrador', 'Contador', 'Operador'}


def persist_import(
    db: Session, *, actor_id: int, company_id: int, competence: str,
    filename: str, size_bytes: int, sha256: str, statement: ParsedStatement,
) -> PayrollImport:
    """Revalidate access, serialize duplicates, and persist one import atomically."""
    with db.begin():
        company = db.scalar(
            select(Company).where(Company.id == company_id).with_for_update()
        )
        if company is None:
            raise HTTPException(status_code=403, detail='Acesso negado')

        actor = db.scalar(
            select(User).options(joinedload(User.role)).where(User.id == actor_id)
        )
        if actor is None or not actor.is_active:
            raise HTTPException(status_code=401, detail='Credenciais inválidas')
        if actor.role.name not in IMPORT_ROLES:
            raise HTTPException(status_code=403, detail='Acesso negado')
        require_company_access(db, company_id, actor)
        if company.status != 'Ativa':
            raise HTTPException(status_code=409, detail='Empresa inativa.')

        existing = db.scalar(select(PayrollImport.id).where(
            PayrollImport.company_id == company_id,
            PayrollImport.competencia == competence,
        ).limit(1))
        if existing is not None:
            raise HTTPException(status_code=409, detail='Esta competência já possui uma importação.')

        people = statement['colaboradores']
        rubric_count = sum(len(person['rubricas']) for person in people)
        imported_at = datetime.now(timezone.utc)
        imported_at_iso = imported_at.isoformat().replace('+00:00', 'Z')
        payroll_import = PayrollImport(
            company_id=company_id,
            competencia=competence,
            arquivo=filename,
            arquivo_sha256=sha256,
            arquivo_bytes=size_bytes,
            quantidade_colaboradores=len(people),
            quantidade_rubricas=rubric_count,
            data_hora=imported_at_iso,
            status='Concluída',
            stored_file_id=None,
            created_by_id=actor_id,
        )
        db.add(payroll_import)
        db.flush()

        for person in people:
            for rubric in person['rubricas']:
                db.add(PayrollLine(
                    company_id=company_id,
                    import_id=payroll_import.id,
                    cpf=person['cpf'],
                    nome=person['nome'],
                    cargo=person['cargo'],
                    codigo_verba=rubric['codigo'],
                    verba=rubric['descricao'],
                    referencia=rubric['referencia'],
                    valor=Decimal(rubric['valor']),
                    tipo=rubric['tipo'],
                    liquido=Decimal(person['liquido']),
                ))
        db.flush()
        write_audit(
            db, actor_id=actor_id, action='payroll_import.created',
            entity='payroll_import', entity_id=payroll_import.id,
            company_id=company_id,
            details={'sha256': sha256, 'employees': len(people), 'rubrics': rubric_count},
            created_at=imported_at,
        )
        db.flush()
        db.refresh(payroll_import)
        return payroll_import
