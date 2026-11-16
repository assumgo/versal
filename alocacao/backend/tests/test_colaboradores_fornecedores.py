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


def test_colaborador_crud(client: TestClient) -> None:
    created = client.post(
        '/api/colaboradores',
        json={
            'nome': 'Ana Souza',
            'email_pessoal': 'ana@example.com',
            'cpf': '529.982.247-25',
            'data_nascimento': '1990-05-12',
            'celular': '(11) 98888-7777',
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body['cpf'] == '52998224725'
    assert body['celular'] == '11988887777'

    listed = client.get('/api/colaboradores')
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.put(
        f"/api/colaboradores/{body['id']}",
        json={'nome': 'Ana Souza Silva', 'celular': '11999990000'},
    )
    assert updated.status_code == 200
    assert updated.json()['nome'] == 'Ana Souza Silva'

    deleted = client.delete(f"/api/colaboradores/{body['id']}")
    assert deleted.status_code == 204


def test_fornecedor_crud(client: TestClient) -> None:
    created = client.post(
        '/api/fornecedores',
        json={
            'razao_social': 'Tech Parts LTDA',
            'nome_fantasia': 'Tech Parts',
            'documento': '11.222.333/0001-81',
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body['documento'] == '11222333000181'

    conflict = client.post(
        '/api/fornecedores',
        json={
            'razao_social': 'Outra',
            'nome_fantasia': 'Outra',
            'documento': '11222333000181',
        },
    )
    assert conflict.status_code == 409

    updated = client.put(
        f"/api/fornecedores/{body['id']}",
        json={'nome_fantasia': 'Tech Parts Brasil'},
    )
    assert updated.status_code == 200
    assert updated.json()['nome_fantasia'] == 'Tech Parts Brasil'

    deleted = client.delete(f"/api/fornecedores/{body['id']}")
    assert deleted.status_code == 204
