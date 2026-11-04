from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreate


def list_rooms(db: Session, user: User) -> list[Room]:
    stmt = select(Room).order_by(Room.name, Room.id)
    if not user.is_admin:
        stmt = stmt.where(Room.is_active.is_(True))
    return list(db.scalars(stmt))


def _save(db: Session, room: Room) -> Room:
    db.add(room)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Já existe uma sala com esse nome.') from None
    db.refresh(room)
    return room


def create_room(db: Session, payload: RoomCreate) -> Room:
    return _save(db, Room(
        name=payload.name, location=payload.location, capacity=payload.capacity, is_active=payload.is_active,
    ))


def update_room(db: Session, room_id: int, payload: RoomCreate) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail='Sala não encontrada')
    room.name = payload.name
    room.location = payload.location
    room.capacity = payload.capacity
    room.is_active = payload.is_active
    return _save(db, room)
