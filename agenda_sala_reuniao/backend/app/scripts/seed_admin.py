"""Create the first administrator explicitly. Development only; no default account."""
import os
import sys

from pydantic import SecretStr, ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


def _credentials(environment: str, name: str | None, email: str | None, password: str | None) -> UserCreate:
    if environment != 'development':
        raise ValueError('Bootstrap permitido somente com ENVIRONMENT=development')
    try:
        return UserCreate(
            name=(name or 'Administrador').strip() or 'Administrador',
            email=email or '',
            password=SecretStr(password or ''),
            is_admin=True,
        )
    except ValidationError:
        raise ValueError(
            'Defina FIRST_ADMIN_EMAIL válido e FIRST_ADMIN_PASSWORD com 12–1024 caracteres',
        ) from None


def bootstrap_admin(db: Session, *, environment: str, name: str | None, email: str | None,
                    password: str | None) -> bool:
    payload = _credentials(environment, name, email, password)
    try:
        db.execute(text('SELECT pg_advisory_xact_lock(48151623)'))
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing is not None and existing.is_active and existing.is_admin:
            db.commit()
            return False
        if db.scalar(select(User.id).limit(1)) is not None:
            raise ValueError('Bootstrap recusado: já existem usuários; use a administração autenticada')
        user = User(
            name=payload.name, email=payload.email,
            password_hash=hash_password(payload.password.get_secret_value()),
            is_admin=True, is_active=True,
        )
        db.add(user)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def main() -> int:
    try:
        settings = get_settings()
        name = os.environ.get('FIRST_ADMIN_NAME')
        email = os.environ.get('FIRST_ADMIN_EMAIL')
        password = os.environ.get('FIRST_ADMIN_PASSWORD')
        _credentials(settings.environment, name, email, password)
        with Session(get_engine()) as db:
            created = bootstrap_admin(
                db, environment=settings.environment, name=name, email=email, password=password,
            )
    except ValidationError:
        print('Configuração inválida; verifique DATABASE_URL e JWT_SECRET_KEY', file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print('Falha no banco; confira a conexão e aplique alembic upgrade head', file=sys.stderr)
        return 1
    print('Administrador criado' if created else 'Administrador já configurado; senha preservada')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
