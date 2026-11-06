from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.routes.companies import AuthorizedCompany, _ip
from app.core.dependencies import Database, require_roles
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.services import appointments

router = APIRouter(prefix='/api/v1/companies/{company_id}/appointments', tags=['appointments'])
Writer = Annotated[User, Depends(require_roles('Administrador', 'Contador', 'Operador'))]
Month = Annotated[str, Query(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')]


@router.get('', response_model=list[AppointmentResponse])
def list_appointments(company: AuthorizedCompany, db: Database, month: Month) -> list[AppointmentResponse]:
    return [AppointmentResponse.model_validate(row) for row in appointments.list_month(db, company.id, month)]


@router.post('', response_model=AppointmentResponse, status_code=201)
def create_appointment(payload: AppointmentCreate, request: Request, actor: Writer,
                       company: AuthorizedCompany, db: Database) -> AppointmentResponse:
    return AppointmentResponse.model_validate(appointments.create(db, company.id, payload, actor, _ip(request)))
