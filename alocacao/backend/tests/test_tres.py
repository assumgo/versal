from datetime import date
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
def client(tmp_path, monkeypatch):
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

    monkeypatch.setattr('app.repositories.tres.TRES_DIR', Path(tmp_path) / 'tres')

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


def _seed_produto_equipamento_colaborador(client: TestClient) -> tuple[int, int]:
    categorias = client.get('/api/categorias').json()
    categoria_id = next(item['id'] for item in categorias if item['nome'] == 'Notebook')
    produto = client.post(
        '/api/produtos',
        json={
            'descricao': 'Notebook TRE',
            'marca': 'Dell',
            'modelo': 'Latitude',
            'categoria_id': categoria_id,
        },
    )
    assert produto.status_code == 201, produto.text
    equipamento = client.post(
        '/api/equipamentos',
        json={
            'produto_id': produto.json()['id'],
            'numero_serie': 'SN-TRE-1',
            'numero_patrimonio': 'PAT-TRE-1',
        },
    )
    assert equipamento.status_code == 201, equipamento.text
    colaborador = client.post(
        '/api/colaboradores',
        json={
            'nome': 'Ana Silva',
            'email_pessoal': 'ana.silva@example.com',
            'cpf': '529.982.247-25',
            'data_nascimento': '1990-01-15',
            'celular': '(62) 99999-1111',
            'ativo': True,
        },
    )
    assert colaborador.status_code == 201, colaborador.text
    return equipamento.json()['id'], colaborador.json()['id']


def test_alocacao_gera_tre_entrega_e_devolucao(client: TestClient) -> None:
    equipamento_id, colaborador_id = _seed_produto_equipamento_colaborador(client)

    created = client.post(
        '/api/alocacoes',
        json={'colaborador_id': colaborador_id, 'equipamento_ids': [equipamento_id]},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body['tre_codigo'] == '000001'
    assert body['tre_tipo'] == 'entrega'
    assert body['alocacoes'][0]['ativa'] is True

    tres = client.get('/api/tres', params={'nome': 'Ana'})
    assert tres.status_code == 200
    assert len(tres.json()) == 1
    assert tres.json()[0]['tipo'] == 'entrega'
    assert tres.json()[0]['colaborador_nome'] == 'Ana Silva'

    pdf = client.get(f"/api/tres/{body['tre_id']}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers['content-type'].startswith('application/pdf')
    assert pdf.content[:4] == b'%PDF'
    import pymupdf

    generated = pymupdf.open(stream=pdf.content, filetype='pdf')
    assert any('TRE Nº 000001' in page.get_text() for page in generated)
    generated.close()

    today = date.today().isoformat()
    filtrado = client.get('/api/tres', params={'codigo': '000001', 'data_inicio': today, 'data_fim': today})
    assert len(filtrado.json()) == 1

    alocacao_id = body['alocacoes'][0]['id']
    devolvido = client.post('/api/alocacoes/devolver', json={'alocacao_ids': [alocacao_id]})
    assert devolvido.status_code == 200, devolvido.text
    assert devolvido.json()['tre_codigo'] == '000002'
    assert devolvido.json()['tre_tipo'] == 'devolucao'
    assert devolvido.json()['alocacoes'][0]['ativa'] is False

    todos = client.get('/api/tres')
    assert len(todos.json()) == 2
    tipos = {item['tipo'] for item in todos.json()}
    assert tipos == {'entrega', 'devolucao'}
