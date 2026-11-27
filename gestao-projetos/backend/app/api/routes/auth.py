from typing import Annotated

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select

from app.core.dependencies import CurrentUser, Database
from app.core.security import create_access_token, verify_password, verify_unknown_account
from app.models.entities import User
from app.schemas.projects import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix='/api/auth', tags=['auth'])


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, name=user.name, email=user.email)


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Database, response: Response) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    valid = verify_password(payload.password, user.password_hash) if user is not None else False
    if user is None:
        verify_unknown_account(payload.password)
    if not valid or user is None:
        raise HTTPException(status_code=401, detail='Credenciais inválidas', headers={'WWW-Authenticate': 'Bearer'})
    response.headers['Cache-Control'] = 'no-store'
    return TokenResponse(access_token=create_access_token(user.id), user=_user_out(user))


@router.get('/me', response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return _user_out(user)
