"""Create development roles and the first administrator, explicitly."""
import os
import sys

from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.security import hash_password
from app.models.user import Role, User
from app.schemas.user import UserCreate
from app.services.audit import write_audit


def _credentials(environment: str, email: str | None, password: str | None) -> UserCreate:
    if environment != 'development':
        raise ValueError('Bootstrap permitido somente com ENVIRONMENT=development')
    try:
        return UserCreate(email=email, password=password, role='Administrador')
    except ValidationError:
        # Never interpolate validation errors: they may contain the password.
        raise ValueError('Defina FIRST_ADMIN_EMAIL válido e FIRST_ADMIN_PASSWORD com 12–1024 caracteres') from None


def bootstrap_admin(db: Session, *, environment: str, email: str | None,
                    password: str | None) -> bool:
    payload = _credentials(environment, email, password)
    try:
        # Serialize even before the first role exists; released on commit/rollback.
        db.execute(text('SELECT pg_advisory_xact_lock(863217406)'))
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing is not None and existing.is_active and existing.role.name == 'Administrador':
            db.commit()
            return False
        if db.scalar(select(User.id).limit(1)) is not None:
            raise ValueError('Bootstrap recusado: já existem usuários; use a administração autenticada')
        roles = {role.name: role for role in db.scalars(select(Role))}
        for name in ('Administrador', 'Contador', 'Operador', 'Consulta'):
            if name not in roles:
                roles[name] = Role(name=name)
                db.add(roles[name])
        user = User(email=payload.email, password_hash=hash_password(payload.password.get_secret_value()),
                    role=roles['Administrador'], is_active=True)
        db.add(user)
        db.flush()
        write_audit(db, actor_id=None, action='user.bootstrap', entity='users', entity_id=user.id)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def main() -> int:
    try:
        settings = get_settings()
        email = os.environ.get('FIRST_ADMIN_EMAIL')
        password = os.environ.get('FIRST_ADMIN_PASSWORD')
        # Validate before obtaining an engine or touching the database.
        _credentials(settings.environment, email, password)
        with Session(get_engine()) as db:
            created = bootstrap_admin(db, environment=settings.environment, email=email, password=password)
    except ValidationError:
        print('Configuração inválida; verifique DATABASE_URL e JWT_SECRET_KEY', file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print('Falha no banco; confira a conexão e aplique alembic upgrade head', file=sys.stderr)
        return 1
    except RuntimeError:
        print('Bootstrap falhou; confira a configuração do banco e a auditoria', file=sys.stderr)
        return 1
    print('Administrador criado' if created else 'Administrador já configurado; senha preservada')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
