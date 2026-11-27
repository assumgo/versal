from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import CurrentUser, Database
from app.core.security import hash_password
from app.core.time import now_utc
from app.models.entities import User
from app.schemas.projects import UserCreate, UserOut

router = APIRouter(prefix='/api/users', tags=['users'])


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, name=user.name, email=user.email)


@router.get('', response_model=list[UserOut])
def list_users(_user: CurrentUser, db: Database) -> list[UserOut]:
    users = db.scalars(select(User).order_by(User.name, User.id))
    return [_user_out(user) for user in users]


@router.post('', response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, _actor: CurrentUser, db: Database) -> UserOut:
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        created_at=now_utc(),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Já existe uma pessoa com esse e-mail.') from None
    db.refresh(user)
    return _user_out(user)
