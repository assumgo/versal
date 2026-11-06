from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.user import User
from app.schemas.appointment import ReservationCreate, ReservationResponse
from app.services.appointments import month_bounds
from app.services.audit import write_audit

ZONE = ZoneInfo('America/Sao_Paulo')


def now_local() -> datetime:
    return datetime.now(ZONE)


def _at(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock.replace(tzinfo=None), ZONE)


def action_label(day: date, ends_at: time, current: datetime | None = None) -> str:
    moment = current or now_local()
    return 'Finalizado' if _at(day, ends_at) <= moment else 'Agendada'


def validate_window(day: date, starts_at: time, ends_at: time) -> None:
    start = _at(day, starts_at)
    end = _at(day, ends_at)
    if end <= start:
        raise HTTPException(status_code=422, detail='O horário final precisa ser depois do início.')
    if end - start > timedelta(hours=2):
        raise HTTPException(status_code=422, detail='O intervalo da reserva não pode passar de 2 horas.')
    if start < now_local() + timedelta(minutes=30):
        raise HTTPException(status_code=422, detail='A reserva precisa começar pelo menos 30 minutos após o horário atual.')


def present(row: Appointment) -> ReservationResponse:
    return ReservationResponse.model_validate({
        'id': row.id,
        'scheduled_date': row.scheduled_date,
        'starts_at': row.starts_at,
        'ends_at': row.ends_at,
        'title': row.title,
        'details': row.details,
        'action': action_label(row.scheduled_date, row.ends_at),
    })


def list_month(db: Session, month: str) -> list[ReservationResponse]:
    start, end = month_bounds(month)
    rows = db.scalars(select(Appointment).where(
        Appointment.company_id.is_(None),
        Appointment.scheduled_date >= start,
        Appointment.scheduled_date < end,
    ).order_by(Appointment.scheduled_date, Appointment.starts_at, Appointment.id))
    return [present(row) for row in rows]


def create(db: Session, payload: ReservationCreate, actor: User, ip: str | None) -> ReservationResponse:
    validate_window(payload.scheduled_date, payload.starts_at, payload.ends_at)
    reservation = Appointment(company_id=None, **payload.model_dump())
    db.add(reservation)
    try:
        db.flush()
        write_audit(db, actor_id=actor.id, company_id=None, action='reservation.create',
                    entity='reservations', entity_id=reservation.id, ip_address=ip,
                    details={'fields': sorted(payload.model_fields_set)})
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(reservation)
    return present(reservation)
