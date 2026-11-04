import os

import pytest
from alembic import command
from alembic.config import Config

from app.core.config import get_settings
from app.core.database import get_engine


def database_url() -> str:
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to disposable, migrated PostgreSQL')
    return url


def migrate(url: str) -> None:
    os.environ['DATABASE_URL'] = url
    get_settings.cache_clear()
    get_engine.cache_clear()
    command.upgrade(Config('alembic.ini'), 'head')
