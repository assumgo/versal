from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_health_returns_ok_without_database() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


async def test_validation_error_omits_password() -> None:
    transport = ASGITransport(app=app)
    secret = 'this-password-must-not-appear'
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.post('/api/v1/auth/login', json={'email': 'ana@agenda.test', 'password': secret, 'extra': secret})
    assert response.status_code == 422
    assert secret not in response.text
