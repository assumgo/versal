import pytest
from sqlalchemy import select

from test_authorization import admin_db, accounts, client, headers, COMPANIES
from app.models.audit import AuditLog
from app.models.company import Company, Employee


@pytest.mark.asyncio
async def test_company_create_update_inactivate_preserves_history(client, accounts, admin_db):
    auth = headers(accounts)
    async with client:
        response = await client.post(COMPANIES, headers=auth, json={
            'razao': 'Nova empresa', 'cnpj': '11.222.333/0001-81'})
        assert response.status_code == 201, response.text
        company_id = response.json()['id']
        assert response.json()['cnpj'] == '11222333000181'
        endpoint = f'{COMPANIES}/{company_id}'
        assert (await client.get(endpoint, headers=auth)).status_code == 200
        updated = await client.patch(endpoint, headers=auth, json={'fantasia': 'Nova'})
        assert updated.status_code == 200
        employee = Employee(company_id=company_id, nome='Histórico')
        admin_db.add(employee)
        admin_db.commit()
        assert (await client.delete(endpoint, headers=auth)).status_code == 204
        assert (await client.delete(endpoint, headers=auth)).status_code == 204
        assert (await client.get(endpoint, headers=auth)).json()['status'] == 'Inativa'
        assert admin_db.get(Employee, employee.id) is not None
    events = admin_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [e.action for e in events] == ['company.create', 'company.update', 'company.inactivate']
    assert all(e.company_id == company_id and e.actor_id == accounts[0]['Administrador'].id
               and e.ip_address == '127.0.0.1' for e in events)


@pytest.mark.asyncio
@pytest.mark.parametrize('cnpj', ['11111111111111', '11222333000180', 'abc11222333000181', '', None])
async def test_invalid_cnpj_does_not_persist(client, accounts, admin_db, cnpj):
    async with client:
        result = await client.post(COMPANIES, headers=headers(accounts),
                                   json={'razao': 'Invalid', 'cnpj': cnpj})
        assert result.status_code == 422
    assert admin_db.scalar(select(Company).where(Company.razao == 'Invalid')) is None
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Contador', 'Operador', 'Consulta'])
async def test_company_writes_require_admin(client, accounts, role):
    endpoint = f'{COMPANIES}/{accounts[1][0].id}'
    async with client:
        for method, path, body in [('POST', COMPANIES, {'razao': 'X', 'cnpj': '11222333000181'}),
                                   ('PATCH', endpoint, {'razao': 'X'}), ('DELETE', endpoint, None)]:
            assert (await client.request(method, path, headers=headers(accounts, role), json=body)).status_code == 403


@pytest.mark.asyncio
async def test_company_update_requires_membership_and_validates_atomically(client, accounts, admin_db):
    async with client:
        assert (await client.patch(f'{COMPANIES}/{accounts[1][1].id}', headers=headers(accounts),
                                   json={'razao': 'Forbidden'})).status_code == 403
        endpoint = f'{COMPANIES}/{accounts[1][0].id}'
        for body in ({'razao': 'Changed', 'cnpj': 'bad'}, {'razao': None}, {'status': 'unknown'}, {'company_id': 2}):
            assert (await client.patch(endpoint, headers=headers(accounts), json=body)).status_code == 422
    admin_db.refresh(accounts[1][0])
    assert accounts[1][0].razao == 'Visible company'
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['create', 'update', 'inactivate'])
async def test_company_mutation_rolls_back_when_audit_fails(client, accounts, admin_db, monkeypatch, operation):
    from app.services import companies

    def fail_audit(*args, **kwargs):
        raise RuntimeError('audit unavailable')

    monkeypatch.setattr(companies, 'write_audit', fail_audit)
    target = accounts[1][0].id
    async with client:
        with pytest.raises(RuntimeError, match='audit unavailable'):
            if operation == 'create':
                await client.post(COMPANIES, headers=headers(accounts), json={'razao': 'Rolled back', 'cnpj': '11222333000181'})
            elif operation == 'update':
                await client.patch(f'{COMPANIES}/{target}', headers=headers(accounts), json={'razao': 'Rolled back'})
            else:
                await client.delete(f'{COMPANIES}/{target}', headers=headers(accounts))
    assert admin_db.scalar(select(Company).where(Company.razao == 'Rolled back')) is None
    company = admin_db.get(Company, target)
    assert company.razao == 'Visible company'
    assert company.status == 'Ativa'
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
async def test_admin_can_reactivate_company(client, accounts, admin_db):
    company = accounts[1][0]
    company.status = 'Inativa'
    admin_db.commit()
    async with client:
        result = await client.patch(f'{COMPANIES}/{company.id}', headers=headers(accounts), json={'status': 'Ativa'})
        assert result.status_code == 200
        assert result.json()['status'] == 'Ativa'
