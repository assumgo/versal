import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_openapi_documents_phase_one_routes_and_bearer_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        schema = (await client.get('/openapi.json')).json()
        expected = {
            '/api/v1/auth/login': {'post'}, '/api/v1/auth/refresh': {'post'},
            '/api/v1/auth/logout': {'post'}, '/api/v1/auth/me': {'get'},
            '/api/v1/users': {'get', 'post'},
            '/api/v1/users/{user_id}': {'get', 'patch', 'delete'},
            '/api/v1/users/{user_id}/companies': {'get'},
            '/api/v1/users/{user_id}/companies/{company_id}': {'put', 'delete'},
            '/api/v1/companies': {'get', 'post'},
            '/api/v1/companies/{company_id}': {'get', 'patch', 'delete'},
            '/api/v1/companies/{company_id}/employees': {'get', 'post'},
            '/api/v1/companies/{company_id}/chart-accounts': {'get', 'post'},
            '/api/v1/companies/{company_id}/competences': {'get'},
            '/api/v1/companies/{company_id}/accounting-review': {'get'},
            '/api/v1/companies/{company_id}/finance-params': {'get', 'post'},
            '/api/v1/companies/{company_id}/rubrics': {'get', 'post'},
            '/api/v1/companies/{company_id}/rubrics/{rubric_id}': {'get', 'patch'},
            '/api/v1/companies/{company_id}/chart-accounts/{account_id}': {'get', 'patch'},
            '/api/v1/companies/{company_id}/employees/{employee_id}': {'get', 'patch', 'delete'},
        }
        for path, methods in expected.items():
            assert methods <= schema['paths'][path].keys(), path
            if '/auth/' not in path or path.endswith('/me'):
                for method in methods:
                    assert schema['paths'][path][method]['security'] == [{'HTTPBearer': []}]
        assert schema['components']['securitySchemes']['HTTPBearer']['scheme'] == 'bearer'
        assert (await client.get('/docs')).status_code == 200


@pytest.mark.asyncio
async def test_cors_allows_configured_origin_with_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.options('/api/v1/companies', headers={
            'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'PATCH',
            'Access-Control-Request-Headers': 'authorization,content-type'})
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'
        assert response.headers['access-control-allow-credentials'] == 'true'
        response = await client.get('/health', headers={'Origin': 'http://localhost:5173'})
        assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'


@pytest.mark.asyncio
async def test_cors_does_not_authorize_unknown_origin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.options('/api/v1/companies', headers={
            'Origin': 'https://untrusted.test', 'Access-Control-Request-Method': 'POST'})
        assert response.status_code == 400
        assert 'access-control-allow-origin' not in response.headers
