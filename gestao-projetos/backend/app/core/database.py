from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if url.startswith('sqlite'):
        engine = create_engine(url, poolclass=StaticPool, connect_args={'check_same_thread': False})
        event.listen(engine, 'connect', _enable_sqlite_foreign_keys)
        return engine
    return create_engine(url, pool_pre_ping=True)


def get_db() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
