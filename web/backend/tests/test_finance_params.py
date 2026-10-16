"""Financial insertion preserves desktop text and permits repeated types."""
import pytest
from sqlalchemy import select

from test_authorization import admin_db, accounts, client, headers, COMPANIES
from app.models import FinanceParam, AuditLog


def endpoint(accounts, private=False):
    return f'{COMPANIES}/{accounts[1][int(private)].id}/finance-params'


@pytest.mark.asyncio
async def test_finance_create_preserves_desktop_fields(client, accounts, admin_db):
    body = {'tipo': ' INSS ', 'documento_id': '0007', 'parceiro_cpf_cnpj': ' 001.234/0001 ',
            'codigo_parceiro_siagri': '0009', 'conta_contrapartida': ' 001.23 ',
            'centro_custo': ' 001 ', 'historico': ' Histórico sem trim '}
    async with client:
        response = await client.post(endpoint(accounts), headers=headers(accounts, 'Contador'), json=body)
        assert response.status_code == 201, response.text
        row = response.json()
        assert {key: row[key] for key in body} == {**body, 'tipo': 'INSS'}
        assert row['vencimento_dia'] == 1 and row['ativo'] == 1
        assert row['company_id'] == accounts[1][0].id
    logs = admin_db.scalars(select(AuditLog).where(AuditLog.entity == 'finance_params')).all()
    assert len(logs) == 1 and logs[0].action == 'finance_param.create'
    assert logs[0].actor_id == accounts[0]['Contador'].id
    assert logs[0].company_id == accounts[1][0].id
    assert 'Histórico sem trim' not in str(logs[0].details)
    assert 'tipo' in logs[0].details['fields']


@pytest.mark.asyncio
async def test_finance_allows_repeated_and_empty_types(client, accounts):
    async with client:
        for body in ({'tipo': 'INSS'}, {'tipo': 'INSS'}, {}):
            response = await client.post(endpoint(accounts), headers=headers(accounts), json=body)
            assert response.status_code == 201, response.text
        page = (await client.get(endpoint(accounts), headers=headers(accounts))).json()
        assert [r['tipo'] for r in page['items']] == ['', 'INSS', 'INSS']
        assert page['total'] == 3 and page['limit'] == 50 and page['offset'] == 0
        assert all(r['documento_id'] == '' for r in page['items'])


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Administrador', 'Contador', 'Operador', 'Consulta'])
async def test_finance_scope_roles_and_inactive_company(client, accounts, admin_db, role):
    auth = headers(accounts, role)
    writer = role in ('Administrador', 'Contador')
    async with client:
        assert (await client.get(endpoint(accounts), headers=auth)).status_code == 200
        assert (await client.get(endpoint(accounts, True), headers=auth)).status_code == 403
        assert (await client.post(endpoint(accounts, True), headers=auth, json={})).status_code == 403
        assert (await client.post(endpoint(accounts), headers=auth, json={})).status_code == (201 if writer else 403)
        accounts[1][0].status = 'Inativa'
        admin_db.commit()
        assert (await client.get(endpoint(accounts), headers=auth)).status_code == 200
        assert (await client.post(endpoint(accounts), headers=auth, json={})).status_code == (409 if writer else 403)


@pytest.mark.asyncio
async def test_finance_legacy_pagination_and_validation(client, accounts, admin_db):
    company = accounts[1][0].id
    legacy = FinanceParam(company_id=company, tipo=None, vencimento_dia=None)
    rows = [FinanceParam(company_id=company, tipo='INSS'), FinanceParam(company_id=company, tipo='INSS')]
    admin_db.add_all([legacy, *rows, FinanceParam(company_id=accounts[1][1].id, tipo='PRIVATE')])
    admin_db.flush()
    legacy.ativo = None
    admin_db.commit()
    async with client:
        path, auth = endpoint(accounts), headers(accounts)
        page = (await client.get(path, headers=auth)).json()
        assert [r['id'] for r in page['items']] == [legacy.id, rows[0].id, rows[1].id]
        assert page['items'][0]['ativo'] is None and page['items'][0]['vencimento_dia'] is None
        assert page['items'][0]['documento_id'] is None
        page = (await client.get(path, headers=auth, params={'offset': 1, 'limit': 1})).json()
        assert page['total'] == 3 and [r['id'] for r in page['items']] == [rows[0].id]
        for query in ({'offset': -1}, {'limit': 0}, {'limit': 101}):
            assert (await client.get(path, headers=auth, params=query)).status_code == 422
        for day in (0, 32, True, '1', None):
            assert (await client.post(path, headers=auth, json={'vencimento_dia': day})).status_code == 422
        for body in ({'company_id': company}, {'ativo': 0}, {'tipo': None}):
            assert (await client.post(path, headers=auth, json=body)).status_code == 422
        for day in (1, 31):
            assert (await client.post(path, headers=auth, json={'vencimento_dia': day})).status_code == 201
        assert (await client.patch(path, headers=auth, json={})).status_code == 405
        assert (await client.delete(path, headers=auth)).status_code == 405


@pytest.mark.asyncio
async def test_finance_audit_failure_rolls_back(client, accounts, admin_db, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('audit unavailable')
    monkeypatch.setattr('app.services.companies.write_audit', fail)
    async with client:
        with pytest.raises(RuntimeError, match='audit unavailable'):
            await client.post(endpoint(accounts), headers=headers(accounts), json={'tipo': 'Rollback'})
    assert admin_db.scalar(select(FinanceParam.id)) is None
