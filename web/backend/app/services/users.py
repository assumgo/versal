from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.company import Company
from app.models.user import Role, User, UserCompany
from app.schemas.user import UserCreate, UserUpdate
from app.services.audit import write_audit


def find_user(db: Session, user_id: int, *, lock: bool = False) -> User:
    query = select(User).where(User.id == user_id)
    user = db.scalar(query.with_for_update() if lock else query)
    if user is None:
        raise HTTPException(status_code=404, detail='Usuário não encontrado')
    return user


def _role(db: Session, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name))
    if role is None:
        raise HTTPException(status_code=422, detail='Papel não configurado')
    return role


def _lock_administrators(db: Session) -> None:
    # Lock a common row BEFORE target-user locks. Locking separate users alone
    # would allow two administrators to remove their access simultaneously.
    db.scalar(select(Role).where(Role.name == 'Administrador').with_for_update())


def _preserve_administrator(db: Session, user: User, *, role: str, is_active: bool) -> None:
    if not user.is_active or user.role.name != 'Administrador':
        return
    if is_active and role == 'Administrador':
        return
    replacement = db.scalar(select(User.id).where(
        User.role_id == user.role_id, User.is_active.is_(True), User.id != user.id).limit(1))
    if replacement is None:
        raise HTTPException(status_code=409, detail='É necessário manter um administrador ativo')


def _save(db: Session, *, actor: User, action: str, entity: str, row: User | UserCompany,
          ip_address: str | None, company_id: int | None = None, details: dict | None = None) -> None:
    try:
        db.flush()
        write_audit(db, actor_id=actor.id, action=action, entity=entity, entity_id=row.id,
                    company_id=company_id, details=details, ip_address=ip_address)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Registro já existente ou vínculo inválido') from None
    except Exception:
        db.rollback()
        raise


def create_user(db: Session, payload: UserCreate, actor: User, ip: str | None) -> User:
    user = User(email=payload.email, password_hash=hash_password(payload.password.get_secret_value()),
                role=_role(db, payload.role), is_active=payload.is_active)
    db.add(user)
    _save(db, actor=actor, action='user.create', entity='users', row=user, ip_address=ip)
    return user


def update_user(db: Session, user_id: int, payload: UserUpdate, actor: User, ip: str | None) -> User:
    _lock_administrators(db)
    user = find_user(db, user_id, lock=True)
    # Resolve the role before changing any fields, preventing partial validation writes.
    role = _role(db, payload.role) if 'role' in payload.model_fields_set else None
    _preserve_administrator(db, user, role=role.name if role else user.role.name,
                            is_active=payload.is_active if 'is_active' in payload.model_fields_set
                            else user.is_active)
    for field in payload.model_fields_set:
        if field == 'role':
            user.role = role
        elif field == 'password':
            user.password_hash = hash_password(payload.password.get_secret_value())
        else:
            setattr(user, field, getattr(payload, field))
    _save(db, actor=actor, action='user.update', entity='users', row=user, ip_address=ip,
          details={'fields': sorted(payload.model_fields_set)})
    return user


def inactivate_user(db: Session, user_id: int, actor: User, ip: str | None) -> None:
    _lock_administrators(db)
    user = find_user(db, user_id, lock=True)
    if user.is_active:
        _preserve_administrator(db, user, role=user.role.name, is_active=False)
        user.is_active = False
        _save(db, actor=actor, action='user.inactivate', entity='users', row=user, ip_address=ip)


def change_membership(db: Session, user_id: int, company_id: int, *, grant: bool,
                      actor: User, ip: str | None) -> None:
    # Serialize membership changes for each target user, including repeated grants.
    find_user(db, user_id, lock=True)
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail='Empresa não encontrada')
    membership = db.scalar(select(UserCompany).where(
        UserCompany.user_id == user_id, UserCompany.company_id == company_id))
    if grant and membership is None:
        membership = UserCompany(user_id=user_id, company_id=company_id)
        db.add(membership)
    elif not grant and membership is not None:
        db.delete(membership)
    else:
        return
    _save(db, actor=actor, action='membership.grant' if grant else 'membership.revoke',
          entity='user_companies', row=membership, company_id=company_id,
          details={'user_id': user_id}, ip_address=ip)
