import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import seed_categorias
from app.db.session import Base, get_db
from app.main import app
from app.models.alocacao import Alocacao


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
        yield test_client, TestingSession
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_equipamento_crud_and_status_filters(client) -> None:
    test_client, TestingSession = client
    categorias = test_client.get('/api/categorias').json()
    categoria_id = next(item['id'] for item in categorias if item['nome'] == 'Notebook')

    created = test_client.post(
        '/api/equipamentos',
        json={
            'descricao': 'Notebook corporativo',
            'marca': 'Dell',
            'modelo': 'Latitude 5440',
            'numero_serie': 'SN-001',
            'numero_patrimonio': 'PAT-001',
            'mac_address': 'AA:BB:CC:DD:EE:FF',
            'categoria_id': categoria_id,
        },
    )
    assert created.status_code == 201, created.text
    equipamento = created.json()
    assert equipamento['status'] == 'disponivel'
    assert equipamento['categoria_nome'] == 'Notebook'

    conflict = test_client.post(
        '/api/equipamentos',
        json={
            'descricao': 'Outro',
            'marca': 'Dell',
            'modelo': 'X',
            'numero_serie': 'SN-002',
            'numero_patrimonio': 'PAT-001',
            'categoria_id': categoria_id,
        },
    )
    assert conflict.status_code == 409

    db = TestingSession()
    db.add(Alocacao(equipamento_id=equipamento['id'], ativa=True))
    db.commit()
    db.close()

    alocados = test_client.get('/api/equipamentos', params={'status': 'alocado'})
    assert alocados.status_code == 200
    assert len(alocados.json()) == 1
    assert alocados.json()[0]['status'] == 'alocado'

    disponiveis = test_client.get('/api/equipamentos', params={'status': 'disponivel'})
    assert disponiveis.status_code == 200
    assert disponiveis.json() == []

    by_cat = test_client.get('/api/equipamentos', params={'categoria_id': categoria_id})
    assert len(by_cat.json()) == 1

    blocked = test_client.delete(f"/api/equipamentos/{equipamento['id']}")
    assert blocked.status_code == 409

    from sqlalchemy import select

    db = TestingSession()
    alocacao = db.scalars(select(Alocacao).where(Alocacao.equipamento_id == equipamento['id'])).one()
    alocacao.ativa = False
    db.add(alocacao)
    db.commit()
    db.close()

    updated = test_client.put(
        f"/api/equipamentos/{equipamento['id']}",
        json={'descricao': 'Notebook atualizado'},
    )
    assert updated.status_code == 200
    assert updated.json()['descricao'] == 'Notebook atualizado'
    assert updated.json()['status'] == 'disponivel'

    deleted = test_client.delete(f"/api/equipamentos/{equipamento['id']}")
    assert deleted.status_code == 204
