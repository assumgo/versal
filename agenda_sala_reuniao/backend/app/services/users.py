from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.name, User.id)))


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password.get_secret_value()),
        is_admin=payload.is_admin,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='E-mail já cadastrado.') from None
    db.refresh(user)
    return user
