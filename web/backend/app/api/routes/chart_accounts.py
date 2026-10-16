from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.routes.companies import AuthorizedCompany, _ip
from app.core.dependencies import Database, Identifier, require_roles
from app.models import User
from app.repositories import chart_accounts as repository
from app.schemas.accounting import Page
from app.schemas.chart_accounts import ChartAccountCreate, ChartAccountResponse, ChartAccountUpdate
from app.services import chart_accounts

router = APIRouter(prefix='/api/v1/companies/{company_id}/chart-accounts', tags=['chart-accounts'])
Writer = Annotated[User, Depends(require_roles('Administrador', 'Contador'))]


@router.get('', response_model=Page[ChartAccountResponse])
def list_accounts(company: AuthorizedCompany, db: Database, q: str = '',
                  offset: Annotated[int, Query(ge=0)] = 0,
                  limit: Annotated[int, Query(ge=1, le=100)] = 50, conta: str | None = None):
    return repository.list_for_company(db, company.id, q=q, offset=offset, limit=limit, conta=conta)


@router.get('/{account_id}', response_model=ChartAccountResponse)
def read_account(account_id: Identifier, company: AuthorizedCompany, db: Database):
    return repository.find(db, company.id, account_id)


@router.post('', response_model=ChartAccountResponse, status_code=201)
def create_account(payload: ChartAccountCreate, request: Request, actor: Writer,
                   company: AuthorizedCompany, db: Database):
    return chart_accounts.create(db, company.id, payload, actor, _ip(request))


@router.patch('/{account_id}', response_model=ChartAccountResponse)
def update_account(account_id: Identifier, payload: ChartAccountUpdate, request: Request,
                   actor: Writer, company: AuthorizedCompany, db: Database):
    return chart_accounts.update(db, company.id, account_id, payload, actor, _ip(request))
