import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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

    produto = test_client.post(
        '/api/produtos',
        json={
            'codigo': 'NB-100',
            'descricao': 'Notebook corporativo',
            'marca': 'Dell',
            'modelo': 'Latitude 5440',
            'categoria_id': categoria_id,
        },
    )
    assert produto.status_code == 201, produto.text
    produto_id = produto.json()['id']

    created = test_client.post(
        '/api/equipamentos',
        json={
            'produto_id': produto_id,
            'numero_serie': 'SN-001',
            'numero_patrimonio': 'PAT-001',
            'mac_address': 'AA:BB:CC:DD:EE:FF',
        },
    )
    assert created.status_code == 201, created.text
    equipamento = created.json()
    assert equipamento['status'] == 'disponivel'
    assert equipamento['produto_codigo'] == 'NB-100'
    assert equipamento['categoria_nome'] == 'Notebook'
    assert 'descricao' not in equipamento or equipamento.get('produto_descricao') == 'Notebook corporativo'

    conflict = test_client.post(
        '/api/equipamentos',
        json={
            'produto_id': produto_id,
            'numero_serie': 'SN-002',
            'numero_patrimonio': 'PAT-001',
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

    blocked_produto = test_client.delete(f'/api/produtos/{produto_id}')
    assert blocked_produto.status_code == 409

    blocked = test_client.delete(f"/api/equipamentos/{equipamento['id']}")
    assert blocked.status_code == 409

    db = TestingSession()
    alocacao = db.scalars(select(Alocacao).where(Alocacao.equipamento_id == equipamento['id'])).one()
    alocacao.ativa = False
    db.add(alocacao)
    db.commit()
    db.close()

    updated = test_client.put(
        f"/api/equipamentos/{equipamento['id']}",
        json={'numero_serie': 'SN-001-B'},
    )
    assert updated.status_code == 200
    assert updated.json()['numero_serie'] == 'SN-001-B'
    assert updated.json()['status'] == 'disponivel'

    deleted = test_client.delete(f"/api/equipamentos/{equipamento['id']}")
    assert deleted.status_code == 204

    deleted_produto = test_client.delete(f'/api/produtos/{produto_id}')
    assert deleted_produto.status_code == 204
