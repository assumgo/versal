from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from app.core.dependencies import Administrator, Database, Reader, require_company_access
from app.models.company import Company
from app.repositories.companies import list_for_user
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services import companies

router = APIRouter(prefix='/api/v1/companies', tags=['companies'])
AuthorizedCompany = Annotated[Company, Depends(require_company_access)]


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get('', response_model=list[CompanyResponse])
def list_companies(user: Reader, db: Database):
    return list_for_user(db, user.id)


@router.post('', response_model=CompanyResponse, status_code=201)
def create_company(payload: CompanyCreate, request: Request, actor: Administrator, db: Database):
    return companies.create(db, payload, actor, _ip(request))


@router.get('/{company_id}', response_model=CompanyResponse)
def read_company(company: AuthorizedCompany):
    return company


@router.patch('/{company_id}', response_model=CompanyResponse)
def update_company(payload: CompanyUpdate, request: Request, actor: Administrator,
                   company: AuthorizedCompany, db: Database):
    return companies.update(db, company.id, payload, actor, _ip(request))


@router.delete('/{company_id}', status_code=204)
def inactivate_company(request: Request, actor: Administrator, company: AuthorizedCompany, db: Database):
    companies.inactivate(db, company.id, actor, _ip(request))
    return Response(status_code=204)
