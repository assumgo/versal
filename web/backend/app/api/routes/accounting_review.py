from typing import Annotated

from fastapi import APIRouter, Query

from app.api.routes.companies import AuthorizedCompany
from app.core.dependencies import Database
from app.repositories import accounting_review
from app.schemas.accounting import Page
from app.schemas.accounting_review import AccountingReviewRow, Competence

router = APIRouter(prefix='/api/v1/companies/{company_id}', tags=['accounting-review'])


@router.get('/competences', response_model=list[str])
def list_competences(company: AuthorizedCompany, db: Database):
    return accounting_review.list_competences(db, company.id)


@router.get('/accounting-review', response_model=Page[AccountingReviewRow])
def review(company: AuthorizedCompany, db: Database, competence: Competence,
           offset: Annotated[int, Query(ge=0)] = 0,
           limit: Annotated[int, Query(ge=1, le=100)] = 50):
    return accounting_review.list_for_company(db, company.id, competence=competence, offset=offset, limit=limit)
