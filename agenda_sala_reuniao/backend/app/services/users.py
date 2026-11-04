from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import RefreshToken, User
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
        must_change_password=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='E-mail já cadastrado.') from None
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=422, detail='Senha atual não confere.')
    if verify_password(new_password, user.password_hash):
        raise HTTPException(status_code=422, detail='A nova senha deve ser diferente da atual.')
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return user


def require_password_change(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=404, detail='Usuário não encontrado.')
    user.must_change_password = True
    db.execute(update(RefreshToken).where(
        RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None),
    ).values(revoked_at=datetime.now(timezone.utc)))
    db.commit()
    db.refresh(user)
    return user
