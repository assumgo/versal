from fastapi import APIRouter, HTTPException

from app.core.dependencies import Administrator, Database, ReadyUser
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.services.rooms import create_room, list_rooms, update_room

router = APIRouter(prefix='/api/v1/rooms', tags=['rooms'])


@router.get('', response_model=list[RoomResponse])
def index(user: ReadyUser, db: Database) -> list[RoomResponse]:
    return [RoomResponse.model_validate(room) for room in list_rooms(db, user)]


@router.post('', response_model=RoomResponse, status_code=201)
def create(payload: RoomCreate, admin: Administrator, db: Database) -> RoomResponse:
    return RoomResponse.model_validate(create_room(db, payload))


@router.patch('/{room_id}', response_model=RoomResponse)
def update(room_id: int, payload: RoomUpdate, admin: Administrator, db: Database) -> RoomResponse:
    if room_id < 1:
        raise HTTPException(status_code=422, detail='Sala inválida')
    return RoomResponse.model_validate(update_room(db, room_id, payload))
