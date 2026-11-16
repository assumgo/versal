from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import seed_categorias
from app.db.session import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path: Path):
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_categorias(db)
    db.close()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_seed_lists_default_categorias(client: TestClient) -> None:
    response = client.get('/api/categorias')
    assert response.status_code == 200
    nomes = [item['nome'] for item in response.json()]
    assert nomes == ['Desktop', 'Monitor', 'Notebook', 'Periféricos', 'Rede', 'Servidor']


def test_create_update_delete_categoria(client: TestClient) -> None:
    created = client.post('/api/categorias', json={'nome': 'Impressora', 'descricao': 'Multifuncionais'})
    assert created.status_code == 201
    categoria_id = created.json()['id']

    conflict = client.post('/api/categorias', json={'nome': 'Impressora'})
    assert conflict.status_code == 409

    updated = client.put(f'/api/categorias/{categoria_id}', json={'descricao': 'Laser e jato de tinta', 'ativo': False})
    assert updated.status_code == 200
    assert updated.json()['descricao'] == 'Laser e jato de tinta'
    assert updated.json()['ativo'] is False

    deleted = client.delete(f'/api/categorias/{categoria_id}')
    assert deleted.status_code == 204
    missing = client.get(f'/api/categorias/{categoria_id}')
    assert missing.status_code == 404
