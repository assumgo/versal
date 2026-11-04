from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

Database = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail='Credenciais inválidas',
                         headers={'WWW-Authenticate': 'Bearer'})


def access_subject(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> int:
    if credentials is None:
        raise unauthorized()
    try:
        return decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise unauthorized() from None


def current_user(subject: Annotated[int, Depends(access_subject)], db: Database) -> User:
    user = db.get(User, subject)
    if user is None or not user.is_active:
        raise unauthorized()
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def ready_user(user: CurrentUser) -> User:
    if user.must_change_password:
        raise HTTPException(status_code=403, detail='Altere a senha antes de continuar.')
    return user


ReadyUser = Annotated[User, Depends(ready_user)]


def require_admin(user: ReadyUser) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail='Acesso negado')
    return user


Administrator = Annotated[User, Depends(require_admin)]
