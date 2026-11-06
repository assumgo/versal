from fastapi import APIRouter

from app.core.dependencies import Database, Reader
from app.schemas.room import RoomResponse
from app.services import reservations

router = APIRouter(prefix='/api/v1/rooms', tags=['rooms'])


@router.get('', response_model=list[RoomResponse])
def list_rooms(db: Database, actor: Reader) -> list[RoomResponse]:
    del actor
    return [RoomResponse.model_validate(room) for room in reservations.list_rooms(db)]
