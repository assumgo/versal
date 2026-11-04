import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_jwt_secret_must_be_at_least_32_characters() -> None:
    with pytest.raises(ValidationError):
        Settings(jwt_secret_key='short')


def test_frontend_origin_rejects_wildcards() -> None:
    with pytest.raises(ValidationError):
        Settings(jwt_secret_key='test-only-secret-with-at-least-32-characters', frontend_origins='*')
