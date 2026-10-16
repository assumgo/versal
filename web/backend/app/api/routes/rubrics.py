from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.routes.companies import AuthorizedCompany, _ip
from app.core.dependencies import Database, Identifier, require_roles
from app.models import User
from app.repositories import rubrics as repository
from app.schemas.accounting import Page
from app.schemas.rubrics import RubricCreate, RubricResponse, RubricStatus, RubricUpdate
from app.services import rubrics

router = APIRouter(prefix='/api/v1/companies/{company_id}/rubrics', tags=['rubrics'])
Writer = Annotated[User, Depends(require_roles('Administrador', 'Contador'))]


@router.get('', response_model=Page[RubricResponse])
def list_rubrics(company: AuthorizedCompany, db: Database, q: str = '',
                 offset: Annotated[int, Query(ge=0)] = 0,
                 limit: Annotated[int, Query(ge=1, le=100)] = 50, status: RubricStatus | None = None):
    return repository.list_for_company(db, company.id, q=q, offset=offset, limit=limit, status=status)


@router.get('/{rubric_id}', response_model=RubricResponse)
def read_rubric(rubric_id: Identifier, company: AuthorizedCompany, db: Database):
    return repository.find(db, company.id, rubric_id)


@router.post('', response_model=RubricResponse, status_code=201)
def create_rubric(payload: RubricCreate, request: Request, actor: Writer,
                  company: AuthorizedCompany, db: Database):
    return rubrics.create(db, company.id, payload, actor, _ip(request))


@router.patch('/{rubric_id}', response_model=RubricResponse)
def update_rubric(rubric_id: Identifier, payload: RubricUpdate, request: Request,
                  actor: Writer, company: AuthorizedCompany, db: Database):
    return rubrics.update(db, company.id, rubric_id, payload, actor, _ip(request))
