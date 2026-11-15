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


def _seed(client: TestClient) -> tuple[int, int, int]:
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
    return equipamento.json()['id'], colaborador.json()['id'], produto.json()['id']


def test_alocacao_colaborador_gera_tre_e_local_nao(client: TestClient) -> None:
    equipamento_id, colaborador_id, produto_id = _seed(client)

    local = client.post('/api/locais', json={'nome': 'Sala TI', 'descricao': 'Estoque interno'})
    assert local.status_code == 201, local.text
    assert local.json()['codigo'] == '000001'

    entrega = client.post(
        '/api/alocacoes',
        json={
            'tipo': 'entrega',
            'destino_tipo': 'colaborador',
            'equipamento_id': equipamento_id,
            'quantidade': 1,
            'colaborador_id': colaborador_id,
            'data_previsao': '2026-11-16',
        },
    )
    assert entrega.status_code == 201, entrega.text
    body = entrega.json()
    assert body['codigo'] == '000001'
    assert body['tipo'] == 'entrega'
    assert body['tre_codigo'] == '000001'
    assert body['data_previsao'] == '2026-11-16'
    assert body['ativa'] is True
    assert body['estoque_disponivel_produto'] == 0

    tres = client.get('/api/tres', params={'nome': 'Ana'})
    assert len(tres.json()) == 1
    assert tres.json()[0]['tipo'] == 'entrega'

    pdf = client.get(f"/api/tres/{body['tre_id']}/pdf")
    assert pdf.status_code == 200
    assert pdf.content[:4] == b'%PDF'
    import pymupdf

    generated = pymupdf.open(stream=pdf.content, filetype='pdf')
    full_text = '\n'.join(page.get_text() for page in generated)
    assert 'Ana Silva' in full_text
    assert 'Entrega de Equipamentos' in full_text
    assert 'Notebook TRE' in full_text or 'Dell' in full_text
    assert '16 de novembro' in full_text
    assert '529.982.247-25' in full_text
    # número do TRE fica no rodapé, não no cabeçalho
    header = generated[0].get_text()[:200]
    assert 'TRE Nº' not in header
    assert 'TRE Nº 000001' in generated[-1].get_text()
    generated.close()

    today = date.today().isoformat()
    filtrado = client.get('/api/tres', params={'codigo': '000001', 'data_inicio': today, 'data_fim': today})
    assert len(filtrado.json()) == 1

    devolucao = client.post(
        '/api/alocacoes',
        json={
            'tipo': 'devolucao',
            'destino_tipo': 'colaborador',
            'equipamento_id': equipamento_id,
            'quantidade': 1,
            'colaborador_id': colaborador_id,
            'data_previsao': '2026-11-16',
        },
    )
    assert devolucao.status_code == 201, devolucao.text
    assert devolucao.json()['codigo'] == '000002'
    assert devolucao.json()['tipo'] == 'devolucao'
    assert devolucao.json()['tre_codigo'] == '000002'
    assert devolucao.json()['ativa'] is False
    assert devolucao.json()['estoque_disponivel_produto'] == 1

    # Novo equipamento para local
    equipamento2 = client.post(
        '/api/equipamentos',
        json={
            'produto_id': produto_id,
            'numero_serie': 'SN-TRE-2',
            'numero_patrimonio': 'PAT-TRE-2',
        },
    )
    assert equipamento2.status_code == 201, equipamento2.text

    local_entrega = client.post(
        '/api/alocacoes',
        json={
            'tipo': 'entrega',
            'destino_tipo': 'local',
            'equipamento_id': equipamento2.json()['id'],
            'quantidade': 1,
            'local_id': local.json()['id'],
        },
    )
    assert local_entrega.status_code == 201, local_entrega.text
    assert local_entrega.json()['tre_id'] is None
    assert local_entrega.json()['destino_nome'] == 'Sala TI'

    todos_tres = client.get('/api/tres')
    assert len(todos_tres.json()) == 2
