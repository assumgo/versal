import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ['JWT_SECRET_KEY'] = 'test-secret-key-with-32-characters'
os.environ['DATABASE_URL'] = 'sqlite+pysqlite://'
os.environ['ENVIRONMENT'] = 'test'
os.environ['SEED_USER_EMAIL'] = ''
os.environ['SEED_USER_PASSWORD'] = ''
os.environ['SEED_USER_NAME'] = ''
os.environ['FRONTEND_ORIGINS'] = 'http://localhost:5174'

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.security import hash_password
from app.core.time import now_utc
from app.models import Base, User
from app.main import app

TODAY = date(2026, 11, 27)


@pytest.fixture
def client(monkeypatch):
    get_settings.cache_clear()
    get_engine.cache_clear()
    monkeypatch.setattr('app.services.projects.clock_today', lambda: TODAY)
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(
            name='Ana Lima',
            email='ana@example.com',
            password_hash=hash_password('senha-segura'),
            created_at=now_utc(),
        ))
        session.commit()
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)
    get_engine.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def auth(client):
    response = client.post('/api/auth/login', json={'email': 'ana@example.com', 'password': 'senha-segura'})
    assert response.status_code == 200, response.text
    token = response.json()['access_token']
    user = response.json()['user']
    return {'Authorization': f'Bearer {token}'}, user
