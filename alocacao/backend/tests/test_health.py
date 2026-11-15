from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_meta_modules() -> None:
    response = client.get('/api/meta')
    assert response.status_code == 200
    body = response.json()
    assert 'notas-fiscais' in body['modules']
    assert body['auth']['provider'] == 'microsoft-entra-id'


def test_dashboard_summary() -> None:
    response = client.get('/api/dashboard/summary')
    assert response.status_code == 200
    body = response.json()
    assert 'disponiveis' in body
    assert 'alocados' in body
    assert 'em_manutencao' in body
    assert 'total_recursos' in body
    assert body['total_recursos'] == body['disponiveis'] + body['alocados']
    assert isinstance(body.get('categorias'), list)
