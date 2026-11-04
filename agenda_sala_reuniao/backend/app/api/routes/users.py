from fastapi import APIRouter, HTTPException

from app.core.dependencies import Administrator, Database
from app.schemas.auth import UserResponse
from app.schemas.user import UserCreate
from app.services.users import create_user, list_users, require_password_change

router = APIRouter(prefix='/api/v1/users', tags=['users'])


@router.get('', response_model=list[UserResponse])
def index(admin: Administrator, db: Database) -> list[UserResponse]:
    return [UserResponse.model_validate(user) for user in list_users(db)]


@router.post('', response_model=UserResponse, status_code=201)
def create(payload: UserCreate, admin: Administrator, db: Database) -> UserResponse:
    return UserResponse.model_validate(create_user(db, payload))


@router.post('/{user_id}/require-password-change', response_model=UserResponse)
def require_change(user_id: int, admin: Administrator, db: Database) -> UserResponse:
    if user_id < 1:
        raise HTTPException(status_code=422, detail='Usuário inválido.')
    return UserResponse.model_validate(require_password_change(db, user_id))
