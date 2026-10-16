from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.company import Company
from app.models.user import User
from app.services.authorization import require_company_access as check_company_access

Database = Annotated[Session, Depends(get_db)]
Identifier = Annotated[int, Path(ge=1, le=9223372036854775807)]
ROLES = ('Administrador', 'Contador', 'Operador', 'Consulta')
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


def require_roles(*names: str) -> Callable[..., User]:
    def check(user: CurrentUser) -> User:
        if user.role.name not in names:
            raise HTTPException(status_code=403, detail='Acesso negado')
        return user

    return check


Administrator = Annotated[User, Depends(require_roles('Administrador'))]
Reader = Annotated[User, Depends(require_roles(*ROLES))]


def require_company_access(company_id: Identifier, user: Reader, db: Database) -> Company:
    return check_company_access(db, company_id, user)
