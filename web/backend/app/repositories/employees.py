from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.company import Employee


def list_for_company(db: Session, company_id: int):
    return db.scalars(select(Employee).where(Employee.company_id == company_id)
                      .order_by(Employee.id)).all()


def find(db: Session, company_id: int, employee_id: int) -> Employee:
    employee = db.scalar(select(Employee).where(
        Employee.company_id == company_id, Employee.id == employee_id))
    if employee is None:
        raise HTTPException(status_code=404, detail='Colaborador não encontrado')
    return employee
