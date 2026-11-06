from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.routes.companies import _ip
from app.core.dependencies import Database, Reader, require_roles
from app.models.user import User
from app.schemas.appointment import ReservationCreate, ReservationResponse
from app.services import reservations

router = APIRouter(prefix='/api/v1/reservations', tags=['reservations'])
Writer = Annotated[User, Depends(require_roles('Administrador', 'Contador', 'Operador'))]
Month = Annotated[str, Query(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')]


@router.get('', response_model=list[ReservationResponse])
def list_reservations(db: Database, month: Month, actor: Reader) -> list[ReservationResponse]:
    del actor
    return reservations.list_month(db, month)


@router.post('', response_model=ReservationResponse, status_code=201)
def create_reservation(payload: ReservationCreate, request: Request, actor: Writer, db: Database) -> ReservationResponse:
    return reservations.create(db, payload, actor, _ip(request))
