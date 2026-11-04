from datetime import datetime, timedelta

from fastapi import HTTPException
from psycopg.errors import ExclusionViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.reservation import Reservation
from app.models.room import Room
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationResponse

CONFLICT = 'Esta sala já está reservada nesse horário.'


def reservation_response(row: Reservation, viewer: User) -> ReservationResponse:
    return ReservationResponse(
        id=row.id, room_id=row.room_id, room_name=row.room.name, user_id=row.user_id,
        user_name=row.organizer.name, title=row.title, starts_at=row.starts_at, ends_at=row.ends_at,
        mine=row.user_id == viewer.id,
    )


def list_reservations(
    db: Session, viewer: User, *, start: datetime, end: datetime, room_id: int | None,
) -> list[ReservationResponse]:
    if end <= start:
        raise HTTPException(status_code=422, detail='O fim da consulta precisa ser posterior ao início')
    if end - start > timedelta(days=31):
        raise HTTPException(status_code=422, detail='O intervalo máximo da consulta é de 31 dias.')
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.room), joinedload(Reservation.organizer))
        .where(Reservation.starts_at < end, Reservation.ends_at > start)
        .order_by(Reservation.starts_at, Reservation.id)
    )
    if room_id is not None:
        stmt = stmt.where(Reservation.room_id == room_id)
    rows = db.scalars(stmt).unique().all()
    return [reservation_response(row, viewer) for row in rows]


def create_reservation(db: Session, user: User, payload: ReservationCreate) -> ReservationResponse:
    room = db.get(Room, payload.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail='Sala não encontrada')
    if not room.is_active:
        raise HTTPException(status_code=422, detail='Sala indisponível')
    row = Reservation(
        room_id=room.id, user_id=user.id, title=payload.title,
        starts_at=payload.starts_at, ends_at=payload.ends_at,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if isinstance(exc.orig, ExclusionViolation):
            raise HTTPException(status_code=409, detail=CONFLICT) from None
        raise
    db.refresh(row)
    row.room = room
    row.organizer = user
    return reservation_response(row, user)


def delete_reservation(db: Session, user: User, reservation_id: int) -> None:
    row = db.get(Reservation, reservation_id)
    if row is None:
        raise HTTPException(status_code=404, detail='Reserva não encontrada')
    if row.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail='Acesso negado')
    db.delete(row)
    db.commit()
