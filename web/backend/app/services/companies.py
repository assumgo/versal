from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.user import User, UserCompany
from app.repositories.companies import lock_company
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.services.audit import write_audit


def save(db: Session, row, actor: User, action: str, entity: str, company_id: int,
         ip: str | None, fields=()) -> None:
    try:
        db.flush()
        write_audit(db, actor_id=actor.id, company_id=company_id, action=action,
                    entity=entity, entity_id=row.id, ip_address=ip,
                    details={'fields': sorted(fields)})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Registro ou vínculo inválido') from None
    except Exception:
        db.rollback()
        raise


def create(db: Session, payload: CompanyCreate, actor: User, ip: str | None) -> Company:
    try:
        company = Company(**payload.model_dump())
        db.add(company)
        db.flush()
        db.add(UserCompany(user_id=actor.id, company_id=company.id))
        save(db, company, actor, 'company.create', 'companies', company.id, ip)
        return company
    except Exception:
        db.rollback()
        raise


def update(db: Session, company_id: int, payload: CompanyUpdate, actor: User, ip: str | None) -> Company:
    company = lock_company(db, company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    save(db, company, actor, 'company.update', 'companies', company_id, ip, payload.model_fields_set)
    return company


def inactivate(db: Session, company_id: int, actor: User, ip: str | None) -> None:
    company = lock_company(db, company_id)
    if company.status != 'Inativa':
        company.status = 'Inativa'
        save(db, company, actor, 'company.inactivate', 'companies', company_id, ip)
