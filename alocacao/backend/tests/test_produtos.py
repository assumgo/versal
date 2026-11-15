import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import seed_categorias
from app.db.session import Base, get_db
from app.main import app


@pytest.fixture()
def client():
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


def test_produto_crud(client: TestClient) -> None:
    categorias = client.get('/api/categorias').json()
    categoria_id = next(item['id'] for item in categorias if item['nome'] == 'Notebook')

    created = client.post(
        '/api/produtos',
        json={
            'codigo': 'NB-001',
            'descricao': 'Notebook corporativo 14"',
            'marca': 'Dell',
            'modelo': 'Latitude 5440',
            'categoria_id': categoria_id,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body['codigo'] == 'NB-001'
    assert body['categoria_nome'] == 'Notebook'

    conflict = client.post(
        '/api/produtos',
        json={
            'codigo': 'NB-001',
            'descricao': 'Outro',
            'marca': 'HP',
            'modelo': 'X',
            'categoria_id': categoria_id,
        },
    )
    assert conflict.status_code == 409

    updated = client.put(f"/api/produtos/{body['id']}", json={'descricao': 'Notebook atualizado'})
    assert updated.status_code == 200
    assert updated.json()['descricao'] == 'Notebook atualizado'

    deleted = client.delete(f"/api/produtos/{body['id']}")
    assert deleted.status_code == 204
