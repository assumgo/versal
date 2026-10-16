import pytest
from sqlalchemy import select

from test_authorization import admin_db, accounts, client, headers, COMPANIES
from app.models.audit import AuditLog
from app.models.company import Employee


def endpoint(accounts, private=False):
    return f'{COMPANIES}/{accounts[1][int(private)].id}/employees'


@pytest.mark.asyncio
async def test_employee_crud_is_scoped_and_audited(client, accounts, admin_db):
    auth = headers(accounts, 'Operador')
    path = endpoint(accounts)
    private = Employee(company_id=accounts[1][1].id, nome='Private')
    admin_db.add(private)
    admin_db.commit()
    async with client:
        created = await client.post(path, headers=auth, json={'nome': 'Ana', 'cpf': '529.982.247-25', 'matricula': '001'})
        assert created.status_code == 201, created.text
        row = created.json()
        assert row['cpf'] == '52998224725'
        assert row['company_id'] == accounts[1][0].id
        target = f"{path}/{row['id']}"
        assert (await client.get(target, headers=auth)).json()['nome'] == 'Ana'
        assert [e['id'] for e in (await client.get(path, headers=auth)).json()] == [row['id']]
        assert (await client.get(f'{path}/{private.id}', headers=auth)).status_code == 404
        updated = await client.patch(target, headers=auth, json={'cargo': 'Analista', 'centro_custo': '10'})
        assert updated.status_code == 200
        assert updated.json()['cargo'] == 'Analista'
        assert (await client.delete(target, headers=auth)).status_code == 204
        assert (await client.get(target, headers=auth)).status_code == 404
    assert admin_db.get(Employee, private.id).nome == 'Private'
    events = admin_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [e.action for e in events] == ['employee.create', 'employee.update', 'employee.delete']
    assert all(e.company_id == accounts[1][0].id and e.entity_id == row['id']
               and e.actor_id == accounts[0]['Operador'].id and e.ip_address == '127.0.0.1' for e in events)
    assert '52998224725' not in str([e.details for e in events])


@pytest.mark.asyncio
@pytest.mark.parametrize('cpf', ['11111111111', '52998224724', 'abc52998224725', '', None])
async def test_invalid_cpf_rejected(client, accounts, admin_db, cpf):
    async with client:
        result = await client.post(endpoint(accounts), headers=headers(accounts, 'Operador'), json={'nome': 'Invalid', 'cpf': cpf})
        assert result.status_code == 422
    assert admin_db.scalars(select(Employee)).all() == []


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Administrador', 'Operador', 'Contador', 'Consulta'])
async def test_employee_permissions_and_cross_company_targets(client, accounts, admin_db, role):
    own = Employee(company_id=accounts[1][0].id, nome='Own', cpf='52998224725')
    other = Employee(company_id=accounts[1][1].id, nome='Private')
    admin_db.add_all([own, other])
    admin_db.commit()
    auth = headers(accounts, role)
    path = endpoint(accounts)
    can_write = role in ('Administrador', 'Operador')
    async with client:
        assert (await client.get(path, headers=auth)).status_code == 200
        for method, suffix, body in [('POST', '', {'nome': 'New', 'cpf': '52998224725'}),
                                     ('PATCH', f'/{other.id}', {'nome': 'Stolen'}), ('DELETE', f'/{other.id}', None)]:
            assert (await client.request(method, endpoint(accounts, True) + suffix, headers=auth, json=body)).status_code == 403
            result = await client.request(method, path + suffix, headers=auth, json=body)
            assert result.status_code == ((201 if method == 'POST' else 404) if can_write else 403)
        if can_write:
            for body in ({'nome': 'Changed', 'cpf': 'bad'}, {'company_id': other.company_id}, {'nome': None}, {'status': 'unknown'}):
                assert (await client.patch(f'{path}/{own.id}', headers=auth, json=body)).status_code == 422
    admin_db.refresh(own)
    admin_db.refresh(other)
    assert own.nome == 'Own'
    assert other.nome == 'Private'


@pytest.mark.asyncio
async def test_inactive_company_allows_history_reads_but_blocks_employee_writes(client, accounts, admin_db):
    company = accounts[1][0]
    company.status = 'Inativa'
    employee = Employee(company_id=company.id, nome='History')
    admin_db.add(employee)
    admin_db.commit()
    path = endpoint(accounts)
    auth = headers(accounts, 'Operador')
    async with client:
        assert (await client.get(path, headers=auth)).status_code == 200
        assert (await client.get(f'{path}/{employee.id}', headers=auth)).status_code == 200
        for method, suffix, body in [('POST', '', {'nome': 'New', 'cpf': '52998224725'}),
                                     ('PATCH', f'/{employee.id}', {'nome': 'Changed'}), ('DELETE', f'/{employee.id}', None)]:
            assert (await client.request(method, path + suffix, headers=auth, json=body)).status_code == 409
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['create', 'update', 'delete'])
async def test_employee_mutation_rolls_back_when_audit_fails(client, accounts, admin_db, monkeypatch, operation):
    from app.services import companies

    employee = Employee(company_id=accounts[1][0].id, nome='Original')
    admin_db.add(employee)
    admin_db.commit()
    employee_id = employee.id

    def fail_audit(*args, **kwargs):
        raise RuntimeError('audit unavailable')

    monkeypatch.setattr(companies, 'write_audit', fail_audit)
    path = endpoint(accounts)
    auth = headers(accounts, 'Operador')
    async with client:
        with pytest.raises(RuntimeError, match='audit unavailable'):
            if operation == 'create':
                await client.post(path, headers=auth, json={'nome': 'Rolled back', 'cpf': '52998224725'})
            elif operation == 'update':
                await client.patch(f'{path}/{employee_id}', headers=auth, json={'nome': 'Rolled back'})
            else:
                await client.delete(f'{path}/{employee_id}', headers=auth)
    assert admin_db.get(Employee, employee_id).nome == 'Original'
    assert admin_db.scalar(select(Employee).where(Employee.nome == 'Rolled back')) is None
    assert admin_db.scalars(select(AuditLog)).all() == []
