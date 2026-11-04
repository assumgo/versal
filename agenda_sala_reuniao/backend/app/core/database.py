from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if not url:
        raise RuntimeError('DATABASE_URL é obrigatória para acessar o banco')
    return create_engine(url, pool_pre_ping=True)


def get_db() -> Generator[Session, None, None]:
    """Provide a request-scoped session; the service owns commit boundaries."""
    with Session(get_engine()) as session:
        yield session
