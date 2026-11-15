from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import seed_categorias
from app.db.session import Base, get_db
from app.main import app


def _client():
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
    return TestClient(app), engine


def test_dashboard_summary_counts_by_status_and_category() -> None:
    client, engine = _client()
    try:
        with client:
            empty = client.get('/api/dashboard/summary')
            assert empty.status_code == 200
            body = empty.json()
            assert body['disponiveis'] == 0
            assert body['alocados'] == 0
            assert body['em_manutencao'] == 0
            assert body['total_recursos'] == 0
            assert len(body['categorias']) >= 1

            categorias = client.get('/api/categorias').json()
            notebook_id = next(item['id'] for item in categorias if item['nome'] == 'Notebook')
            monitor_id = next(item['id'] for item in categorias if item['nome'] == 'Monitor')

            produto_nb = client.post(
                '/api/produtos',
                json={
                    'descricao': 'Notebook Dash',
                    'marca': 'Dell',
                    'modelo': 'Lat',
                    'categoria_id': notebook_id,
                },
            )
            assert produto_nb.status_code == 201
            produto_mon = client.post(
                '/api/produtos',
                json={
                    'descricao': 'Monitor Dash',
                    'marca': 'LG',
                    'modelo': '27',
                    'categoria_id': monitor_id,
                },
            )
            assert produto_mon.status_code == 201

            eq1 = client.post(
                '/api/equipamentos',
                json={
                    'produto_id': produto_nb.json()['id'],
                    'numero_serie': 'SN-D1',
                    'numero_patrimonio': 'PAT-D1',
                },
            )
            eq2 = client.post(
                '/api/equipamentos',
                json={
                    'produto_id': produto_nb.json()['id'],
                    'numero_serie': 'SN-D2',
                    'numero_patrimonio': 'PAT-D2',
                },
            )
            eq3 = client.post(
                '/api/equipamentos',
                json={
                    'produto_id': produto_mon.json()['id'],
                    'numero_serie': 'SN-D3',
                    'numero_patrimonio': 'PAT-D3',
                },
            )
            assert eq1.status_code == 201
            assert eq2.status_code == 201
            assert eq3.status_code == 201

            colaborador = client.post(
                '/api/colaboradores',
                json={
                    'nome': 'Dash User',
                    'email_pessoal': 'dash@example.com',
                    'cpf': '390.533.447-05',
                    'data_nascimento': '1991-02-02',
                    'celular': '(62) 98888-0000',
                    'ativo': True,
                },
            )
            assert colaborador.status_code == 201

            entrega = client.post(
                '/api/alocacoes',
                json={
                    'tipo': 'entrega',
                    'destino_tipo': 'colaborador',
                    'equipamento_id': eq1.json()['id'],
                    'quantidade': 1,
                    'colaborador_id': colaborador.json()['id'],
                    'data_previsao': '2026-11-20',
                },
            )
            assert entrega.status_code == 201, entrega.text

            manut = client.post(
                '/api/alocacoes',
                json={
                    'tipo': 'entrega',
                    'destino_tipo': 'manutencao',
                    'equipamento_id': eq2.json()['id'],
                    'quantidade': 1,
                },
            )
            assert manut.status_code == 201, manut.text

            summary = client.get('/api/dashboard/summary')
            assert summary.status_code == 200
            data = summary.json()
            assert data['disponiveis'] == 1
            assert data['alocados'] == 1
            assert data['em_manutencao'] == 1
            assert data['total_recursos'] == 2  # disponivel + alocado

            by_name = {item['nome']: item for item in data['categorias']}
            assert by_name['Notebook']['disponiveis'] == 0
            assert by_name['Notebook']['alocados'] == 1
            assert by_name['Notebook']['em_manutencao'] == 1
            assert by_name['Notebook']['total'] == 1
            assert by_name['Monitor']['disponiveis'] == 1
            assert by_name['Monitor']['alocados'] == 0
            assert by_name['Monitor']['total'] == 1
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
