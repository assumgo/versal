from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from app.api.routes.companies import AuthorizedCompany, _ip
from app.core.dependencies import Database, Identifier, require_roles
from app.models.user import User
from app.repositories import employees as repository
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.services import employees

router = APIRouter(prefix='/api/v1/companies/{company_id}/employees', tags=['employees'])
Writer = Annotated[User, Depends(require_roles('Administrador', 'Operador'))]


@router.get('', response_model=list[EmployeeResponse])
def list_employees(company: AuthorizedCompany, db: Database):
    return repository.list_for_company(db, company.id)


@router.get('/{employee_id}', response_model=EmployeeResponse)
def read_employee(employee_id: Identifier, company: AuthorizedCompany, db: Database):
    return repository.find(db, company.id, employee_id)


@router.post('', response_model=EmployeeResponse, status_code=201)
def create_employee(payload: EmployeeCreate, request: Request, actor: Writer,
                    company: AuthorizedCompany, db: Database):
    return employees.create(db, company.id, payload, actor, _ip(request))


@router.patch('/{employee_id}', response_model=EmployeeResponse)
def update_employee(employee_id: Identifier, payload: EmployeeUpdate, request: Request,
                    actor: Writer, company: AuthorizedCompany, db: Database):
    return employees.update(db, company.id, employee_id, payload, actor, _ip(request))


@router.delete('/{employee_id}', status_code=204)
def delete_employee(employee_id: Identifier, request: Request, actor: Writer,
                    company: AuthorizedCompany, db: Database):
    employees.delete(db, company.id, employee_id, actor, _ip(request))
    return Response(status_code=204)
