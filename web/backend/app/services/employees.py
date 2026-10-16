from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.company import Employee
from app.models.user import User
from app.repositories.companies import lock_company
from app.repositories.employees import find
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.companies import save


def require_active(db: Session, company_id: int) -> None:
    # Same lock as company inactivation: no write can race past an inactivation.
    company = lock_company(db, company_id)
    if company.status != 'Ativa':
        raise HTTPException(status_code=409, detail='Empresa inativa')


def create(db: Session, company_id: int, payload: EmployeeCreate, actor: User, ip: str | None) -> Employee:
    require_active(db, company_id)
    employee = Employee(company_id=company_id, **payload.model_dump())
    db.add(employee)
    save(db, employee, actor, 'employee.create', 'employees', company_id, ip)
    return employee


def update(db: Session, company_id: int, employee_id: int, payload: EmployeeUpdate,
           actor: User, ip: str | None) -> Employee:
    require_active(db, company_id)
    employee = find(db, company_id, employee_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    save(db, employee, actor, 'employee.update', 'employees', company_id, ip, payload.model_fields_set)
    return employee


def delete(db: Session, company_id: int, employee_id: int, actor: User, ip: str | None) -> None:
    require_active(db, company_id)
    employee = find(db, company_id, employee_id)
    db.delete(employee)
    save(db, employee, actor, 'employee.delete', 'employees', company_id, ip)
