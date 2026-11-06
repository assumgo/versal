from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.user import User
from app.repositories.companies import lock_company
from app.schemas.appointment import AppointmentCreate
from app.services.companies import save


def month_bounds(month: str) -> tuple[date, date]:
    year, number = (int(part) for part in month.split('-'))
    start = date(year, number, 1)
    end = date(year + 1, 1, 1) if number == 12 else date(year, number + 1, 1)
    return start, end


def list_month(db: Session, company_id: int, month: str) -> list[Appointment]:
    start, end = month_bounds(month)
    return list(db.scalars(select(Appointment).where(
        Appointment.company_id == company_id,
        Appointment.scheduled_date >= start,
        Appointment.scheduled_date < end,
    ).order_by(Appointment.scheduled_date, Appointment.starts_at, Appointment.id)))


def create(db: Session, company_id: int, payload: AppointmentCreate, actor: User, ip: str | None) -> Appointment:
    company = lock_company(db, company_id)
    if company.status != 'Ativa':
        raise HTTPException(status_code=409, detail='Empresa inativa')
    appointment = Appointment(company_id=company_id, **payload.model_dump())
    db.add(appointment)
    save(db, appointment, actor, 'appointment.create', 'appointments', company_id, ip,
         payload.model_fields_set)
    return appointment
