"""Explicit, atomic bootstrap preserving existing accounts."""
import importlib

import pytest
from sqlalchemy import select

from test_authorization import admin_db
from app.core.security import verify_password
from app.models.audit import AuditLog
from app.models.user import Role, User

EMAIL = 'first-admin@bootstrap.test'
PASSWORD = 'synthetic-bootstrap-password!'


def bootstrap(db, **overrides):
    module = importlib.import_module('app.scripts.seed_admin')
    options = dict(environment='development', email=EMAIL, password=PASSWORD)
    return module.bootstrap_admin(db, **(options | overrides))


def test_bootstrap_creates_roles_active_admin_and_audit(admin_db):
    assert bootstrap(admin_db) is True
    assert set(admin_db.scalars(select(Role.name))) == {'Administrador', 'Contador', 'Operador', 'Consulta'}
    user = admin_db.scalar(select(User).where(User.email == EMAIL))
    assert user.is_active and user.role.name == 'Administrador'
    assert user.password_hash != PASSWORD
    assert verify_password(PASSWORD, user.password_hash)
    event = admin_db.scalar(select(AuditLog))
    assert event.action == 'user.bootstrap' and event.entity_id == user.id
    assert event.actor_id is None
    assert PASSWORD not in str(event.details) and user.password_hash not in str(event.details)


def test_bootstrap_repeat_preserves_password_and_audit(admin_db):
    bootstrap(admin_db)
    original_hash = admin_db.scalar(select(User)).password_hash
    assert bootstrap(admin_db, password='another-synthetic-password') is False
    assert admin_db.scalar(select(User)).password_hash == original_hash
    assert len(admin_db.scalars(select(User)).all()) == 1
    assert len(admin_db.scalars(select(AuditLog)).all()) == 1


@pytest.mark.parametrize('existing_role,active,email', [
    ('Consulta', True, EMAIL), ('Administrador', False, EMAIL),
    ('Administrador', True, 'other@bootstrap.test')])
def test_bootstrap_refuses_promotion_reactivation_or_another_account(admin_db, existing_role, active, email):
    user = User(email=email, password_hash='preserve', role=Role(name=existing_role), is_active=active)
    admin_db.add(user)
    admin_db.commit()
    with pytest.raises(ValueError):
        bootstrap(admin_db)
    admin_db.refresh(user)
    assert user.password_hash == 'preserve' and user.is_active == active
    assert user.role.name == existing_role
    assert len(admin_db.scalars(select(Role)).all()) == 1
    assert admin_db.scalars(select(AuditLog)).all() == []


def test_bootstrap_rolls_back_when_audit_fails(admin_db, monkeypatch):
    module = importlib.import_module('app.scripts.seed_admin')

    def fail_audit(*args, **kwargs):
        raise RuntimeError('audit unavailable')

    monkeypatch.setattr(module, 'write_audit', fail_audit)
    with pytest.raises(RuntimeError, match='audit unavailable'):
        bootstrap(admin_db)
    assert admin_db.scalars(select(User)).all() == []
    assert admin_db.scalars(select(Role)).all() == []


@pytest.mark.parametrize('environment', ['production', 'staging', 'test'])
def test_command_refuses_non_development_before_database_access(monkeypatch, capsys, environment):
    module = importlib.import_module('app.scripts.seed_admin')
    from app.core.config import get_settings
    monkeypatch.setenv('ENVIRONMENT', environment)
    monkeypatch.setenv('DATABASE_URL', 'invalid-no-database-access')
    monkeypatch.setenv('FIRST_ADMIN_EMAIL', EMAIL)
    monkeypatch.setenv('FIRST_ADMIN_PASSWORD', PASSWORD)
    get_settings.cache_clear()
    try:
        assert module.main() == 1
        output = capsys.readouterr()
        assert 'development' in output.err
        assert PASSWORD not in output.err + output.out
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize('email,password', [(None, None), (EMAIL, None), ('invalid', PASSWORD), (EMAIL, 'short')])
def test_command_rejects_missing_or_invalid_credentials_without_leaking(monkeypatch, capsys, email, password):
    module = importlib.import_module('app.scripts.seed_admin')
    from app.core.config import get_settings
    monkeypatch.setenv('ENVIRONMENT', 'development')
    monkeypatch.setenv('DATABASE_URL', 'invalid-no-database-access')
    for name, value in [('FIRST_ADMIN_EMAIL', email), ('FIRST_ADMIN_PASSWORD', password)]:
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    try:
        assert module.main() == 1
        output = capsys.readouterr()
        assert 'FIRST_ADMIN' in output.err
        if password:
            assert password not in output.err + output.out
    finally:
        get_settings.cache_clear()
