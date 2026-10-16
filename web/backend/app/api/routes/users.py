from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from app.core.dependencies import Administrator, Database, Identifier
from app.models.user import User, UserCompany
from app.schemas.auth import UserResponse
from app.schemas.user import MembershipResponse, UserCreate, UserUpdate, user_response
from app.services import users

router = APIRouter(prefix='/api/v1/users', tags=['users'])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get('', response_model=list[UserResponse])
def list_users(actor: Administrator, db: Database) -> list[UserResponse]:
    return [user_response(user) for user in db.scalars(select(User).order_by(User.id))]


@router.post('', response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, request: Request, actor: Administrator, db: Database) -> UserResponse:
    return user_response(users.create_user(db, payload, actor, _ip(request)))


@router.get('/{user_id}', response_model=UserResponse)
def read_user(user_id: Identifier, actor: Administrator, db: Database) -> UserResponse:
    return user_response(users.find_user(db, user_id))


@router.patch('/{user_id}', response_model=UserResponse)
def update_user(user_id: Identifier, payload: UserUpdate, request: Request,
                actor: Administrator, db: Database) -> UserResponse:
    return user_response(users.update_user(db, user_id, payload, actor, _ip(request)))


@router.delete('/{user_id}', status_code=204)
def inactivate_user(user_id: Identifier, request: Request, actor: Administrator, db: Database) -> Response:
    users.inactivate_user(db, user_id, actor, _ip(request))
    return Response(status_code=204)


@router.get('/{user_id}/companies', response_model=list[MembershipResponse])
def list_memberships(user_id: Identifier, actor: Administrator, db: Database) -> list[MembershipResponse]:
    users.find_user(db, user_id)
    return [MembershipResponse(company_id=row.company_id) for row in db.scalars(
        select(UserCompany).where(UserCompany.user_id == user_id).order_by(UserCompany.company_id))]


@router.put('/{user_id}/companies/{company_id}', status_code=204)
def grant_membership(user_id: Identifier, company_id: Identifier, request: Request,
                     actor: Administrator, db: Database) -> Response:
    users.change_membership(db, user_id, company_id, grant=True, actor=actor, ip=_ip(request))
    return Response(status_code=204)


@router.delete('/{user_id}/companies/{company_id}', status_code=204)
def revoke_membership(user_id: Identifier, company_id: Identifier, request: Request,
                      actor: Administrator, db: Database) -> Response:
    users.change_membership(db, user_id, company_id, grant=False, actor=actor, ip=_ip(request))
    return Response(status_code=204)
