from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Response

from app.core.dependencies import CurrentUser, Database
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.services.reservations import create_reservation, delete_reservation, list_reservations

router = APIRouter(prefix='/api/v1/reservations', tags=['reservations'])


@router.get('', response_model=list[ReservationResponse])
def index(
    user: CurrentUser, db: Database,
    start: datetime = Query(alias='from'),
    end: datetime = Query(alias='to'),
    room_id: int | None = Query(default=None, ge=1),
) -> list[ReservationResponse]:
    if start.tzinfo is None or end.tzinfo is None:
        raise HTTPException(status_code=422, detail='Informe horários com fuso horário')
    return list_reservations(db, user, start=start, end=end, room_id=room_id)


@router.post('', response_model=ReservationResponse, status_code=201)
def create(payload: ReservationCreate, user: CurrentUser, db: Database) -> ReservationResponse:
    return create_reservation(db, user, payload)


@router.delete('/{reservation_id}', status_code=204)
def destroy(reservation_id: int, user: CurrentUser, db: Database) -> Response:
    if reservation_id < 1:
        raise HTTPException(status_code=422, detail='Reserva inválida')
    delete_reservation(db, user, reservation_id)
    return Response(status_code=204)
