from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.dependencies import Database, Reader, require_company_access
from app.models.company import Company
from app.models.user import UserCompany
from app.schemas.company import CompanyResponse

router = APIRouter(prefix='/api/v1/companies', tags=['companies'])


@router.get('', response_model=list[CompanyResponse])
def list_companies(user: Reader, db: Database) -> list[CompanyResponse]:
    return [CompanyResponse.model_validate(company) for company in db.scalars(
        select(Company).join(UserCompany).where(
            UserCompany.user_id == user.id).order_by(Company.id))]


@router.get('/{company_id}', response_model=CompanyResponse)
def read_company(company: Annotated[Company, Depends(require_company_access)]) -> CompanyResponse:
    return CompanyResponse.model_validate(company)
