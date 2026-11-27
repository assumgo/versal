from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.core.time import now_utc
from app.models.entities import User
from app.services.catalog import ensure_templates


def ensure_seed_user(session: Session) -> None:
    settings = get_settings()
    if not settings.seed_user_email or not settings.seed_user_password or not settings.seed_user_name:
        return
    email = settings.seed_user_email.strip().lower()
    existing = session.scalar(select(User).where(User.email == email))
    if existing is not None:
        return
    session.add(User(
        name=settings.seed_user_name.strip(),
        email=email,
        password_hash=hash_password(settings.seed_user_password),
        created_at=now_utc(),
    ))
    session.flush()


def ensure_ready(session: Session) -> None:
    ensure_templates(session)
    ensure_seed_user(session)
