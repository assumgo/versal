import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Only tests receive this non-production key; normal startup requires configuration.
os.environ.setdefault('JWT_SECRET_KEY', 'test-only-secret-with-at-least-32-characters')
os.environ.setdefault('ENVIRONMENT', 'development')

from tests.db import database_url, migrate  # noqa: E402


@pytest.fixture
def agenda_db() -> Iterator[Session]:
    url = database_url()
    migrate(url)
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                with Session(bind=connection, join_transaction_mode='create_savepoint') as session:
                    yield session
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
