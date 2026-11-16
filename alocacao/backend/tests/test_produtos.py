from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

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


def test_produto_codigo_automatico_e_unico(client: TestClient) -> None:
    categorias = client.get('/api/categorias').json()
    categoria_id = next(item['id'] for item in categorias if item['nome'] == 'Notebook')

    first = client.post(
        '/api/produtos',
        json={
            'descricao': 'Notebook corporativo 14"',
            'marca': 'Dell',
            'modelo': 'Latitude 5440',
            'categoria_id': categoria_id,
        },
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert body['codigo'] == '000001'
    assert body['categoria_nome'] == 'Notebook'

    second = client.post(
        '/api/produtos',
        json={
            'descricao': 'Notebook 2',
            'marca': 'HP',
            'modelo': 'ProBook',
            'categoria_id': categoria_id,
        },
    )
    assert second.status_code == 201, second.text
    assert second.json()['codigo'] == '000002'

    updated = client.put(
        f"/api/produtos/{body['id']}",
        json={'descricao': 'Notebook atualizado', 'codigo': '999999'},
    )
    assert updated.status_code == 200
    assert updated.json()['descricao'] == 'Notebook atualizado'
    assert updated.json()['codigo'] == '000001'

    deleted = client.delete(f"/api/produtos/{body['id']}")
    assert deleted.status_code == 204
