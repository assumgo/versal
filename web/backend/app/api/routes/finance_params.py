from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.routes.companies import AuthorizedCompany, _ip
from app.core.dependencies import Database, require_roles
from app.models import User
from app.repositories import finance_params as repository
from app.schemas.accounting import Page
from app.schemas.finance_params import FinanceParamCreate, FinanceParamResponse
from app.services import finance_params

router = APIRouter(prefix='/api/v1/companies/{company_id}/finance-params', tags=['finance-params'])
Writer = Annotated[User, Depends(require_roles('Administrador', 'Contador'))]


@router.get('', response_model=Page[FinanceParamResponse])
def list_params(company: AuthorizedCompany, db: Database,
                offset: Annotated[int, Query(ge=0)] = 0,
                limit: Annotated[int, Query(ge=1, le=100)] = 50):
    return repository.list_for_company(db, company.id, offset=offset, limit=limit)


@router.post('', response_model=FinanceParamResponse, status_code=201)
def create_param(payload: FinanceParamCreate, request: Request, actor: Writer,
                 company: AuthorizedCompany, db: Database):
    return finance_params.create(db, company.id, payload, actor, _ip(request))
