import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password, verify_unknown_account
from app.models.user import RefreshToken, User
from app.services.audit import write_audit


class AuthenticationError(Exception):
    pass


@dataclass(frozen=True)
class TokenPair:
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _issue(db: Session, user: User, family_id: UUID) -> TokenPair:
    raw = secrets.token_urlsafe(48)
    db.add(RefreshToken(user_id=user.id, token_hash=_digest(raw), family_id=family_id,
                        expires_at=datetime.now(timezone.utc) + timedelta(
                            days=get_settings().refresh_token_expire_days)))
    return TokenPair(create_access_token(user.id), raw)


def _audit(db: Session, user: User, action: str, ip_address: str | None) -> None:
    write_audit(db, actor_id=user.id, action=action, entity='users',
                entity_id=user.id, ip_address=ip_address)


def authenticate(db: Session, email: str, password: str, *,
                 ip_address: str | None = None) -> TokenPair:
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    if user is None:
        verify_unknown_account(password)
        raise AuthenticationError()
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise AuthenticationError()
    pair = _issue(db, user, uuid4())
    _audit(db, user, 'auth.login', ip_address)
    db.commit()
    return pair


def _locked_token(db: Session, raw: str) -> tuple[User, RefreshToken]:
    owner_id = db.scalar(select(RefreshToken.user_id).where(RefreshToken.token_hash == _digest(raw)))
    if owner_id is None:
        raise AuthenticationError()
    # Lock the user first to serialize rotation/replay/logout across the family.
    user = db.scalar(select(User).where(User.id == owner_id).with_for_update())
    token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == _digest(raw))
                      .with_for_update().execution_options(populate_existing=True))
    if user is None or token is None:
        raise AuthenticationError()
    return user, token


def rotate_refresh(db: Session, raw_token: str, *,
                   ip_address: str | None = None) -> TokenPair:
    user, token = _locked_token(db, raw_token)
    now = datetime.now(timezone.utc)
    if token.revoked_at is not None:
        db.execute(update(RefreshToken).where(
            RefreshToken.family_id == token.family_id, RefreshToken.revoked_at.is_(None),
        ).values(revoked_at=now))
        _audit(db, user, 'auth.refresh_reuse', ip_address)
        # Revocation must survive the rejected request.
        db.commit()
        raise AuthenticationError()
    if token.expires_at <= now or not user.is_active:
        raise AuthenticationError()
    token.revoked_at = now
    pair = _issue(db, user, token.family_id)
    _audit(db, user, 'auth.refresh', ip_address)
    db.commit()
    return pair


def revoke_refresh(db: Session, raw_token: str, *, ip_address: str | None = None) -> None:
    try:
        user, token = _locked_token(db, raw_token)
    except AuthenticationError:
        return
    # End this entire session, including a successor created by a concurrent refresh.
    db.execute(update(RefreshToken).where(
        RefreshToken.family_id == token.family_id, RefreshToken.revoked_at.is_(None),
    ).values(revoked_at=datetime.now(timezone.utc)))
    _audit(db, user, 'auth.logout', ip_address)
    db.commit()
