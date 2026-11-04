import importlib

import pytest
from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User

EMAIL = 'first-admin@agenda.test'
PASSWORD = 'synthetic-bootstrap-password!'


def bootstrap(db, **overrides):
    module = importlib.import_module('app.scripts.seed_admin')
    options = dict(environment='development', name='Ada', email=EMAIL, password=PASSWORD)
    return module.bootstrap_admin(db, **(options | overrides))


def test_bootstrap_creates_active_admin(agenda_db):
    assert bootstrap(agenda_db) is True
    user = agenda_db.scalar(select(User).where(User.email == EMAIL))
    assert user.name == 'Ada' and user.is_admin and user.is_active
    assert user.password_hash != PASSWORD
    assert verify_password(PASSWORD, user.password_hash)


def test_bootstrap_repeat_preserves_password(agenda_db):
    bootstrap(agenda_db)
    original = agenda_db.scalar(select(User)).password_hash
    assert bootstrap(agenda_db, password='another-synthetic-password') is False
    assert agenda_db.scalar(select(User)).password_hash == original
    assert len(agenda_db.scalars(select(User)).all()) == 1


def test_bootstrap_refuses_when_another_account_exists(agenda_db):
    agenda_db.add(User(name='Outra', email='other@agenda.test', password_hash='preserve', is_admin=False, is_active=True))
    agenda_db.commit()
    with pytest.raises(ValueError, match='já existem usuários'):
        bootstrap(agenda_db)
    assert agenda_db.scalar(select(User).where(User.email == 'other@agenda.test')).password_hash == 'preserve'


@pytest.mark.parametrize('environment', ['production', 'staging', 'test'])
def test_command_refuses_non_development_before_database_access(monkeypatch, capsys, environment):
    module = importlib.import_module('app.scripts.seed_admin')
    monkeypatch.setenv('ENVIRONMENT', environment)
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://invalid:invalid@127.0.0.1:1/none')
    monkeypatch.setenv('FIRST_ADMIN_EMAIL', EMAIL)
    monkeypatch.setenv('FIRST_ADMIN_PASSWORD', PASSWORD)
    from app.core.config import get_settings
    get_settings.cache_clear()
    try:
        assert module.main() == 1
        assert 'somente com ENVIRONMENT=development' in capsys.readouterr().err
    finally:
        get_settings.cache_clear()
