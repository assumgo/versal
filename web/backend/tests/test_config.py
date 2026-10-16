import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_jwt_secret_is_required(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("secret", ["", "short", " " * 32])
def test_jwt_secret_rejects_weak_values(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret_key=secret)


def test_settings_accept_explicit_secret():
    settings = Settings(_env_file=None, jwt_secret_key="test-only-secret-with-at-least-32-characters")
    assert settings.access_token_expire_minutes == 15
