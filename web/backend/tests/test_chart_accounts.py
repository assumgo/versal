import pytest
from sqlalchemy import select

from test_authorization import admin_db, accounts, client, headers, COMPANIES
from app.models import ChartAccount, Rubric
from app.models.audit import AuditLog


def endpoint(accounts, private=False):
    return f'{COMPANIES}/{accounts[1][int(private)].id}/chart-accounts'


@pytest.mark.asyncio
async def test_chart_accounts_are_scoped_paginated_and_audited(client, accounts, admin_db):
    path = endpoint(accounts)
    auth = headers(accounts, 'Contador')
    async with client:
        created = await client.post(path, headers=auth, json={'conta': '4.211.020.001', 'descricao': 'Salários', 'utiliza_cc': 1, 'tipo_correntista': '2-Parceiro'})
        assert created.status_code == 201, created.text
        row = created.json()
        assert row['conta'] == '4211020001'
        assert row['gera_cor'] == 1
        assert (await client.get(f'{path}/{row["id"]}', headers=auth)).json() == row
        rubric = Rubric(company_id=accounts[1][0].id, codigo='01', conta_debito=row['conta'], debito_gera_cor=0)
        admin_db.add(rubric)
        admin_db.commit()
        changed = await client.patch(f'{path}/{row["id"]}', headers=auth, json={'descricao': 'Nova descrição'})
        assert changed.status_code == 200
        assert changed.json()['gera_cor'] == 1
        changed = await client.patch(f'{path}/{row["id"]}', headers=auth, json={'tipo_correntista': '9-Nenhum'})
        assert changed.json()['gera_cor'] == 0
        admin_db.refresh(rubric)
        assert rubric.debito_gera_cor == 0
        result = (await client.get(path, headers=auth)).json()
        assert result['total'] == 1 and result['limit'] == 50 and result['offset'] == 0
        assert len(result['items']) == 1
        assert (await client.delete(f'{path}/{row["id"]}', headers=auth)).status_code == 405
    events = admin_db.scalars(select(AuditLog).where(AuditLog.entity == 'chart_accounts').order_by(AuditLog.id)).all()
    assert [event.action for event in events] == ['chart_account.create', 'chart_account.update', 'chart_account.update']
    assert all(e.company_id == accounts[1][0].id and e.actor_id == accounts[0]['Contador'].id for e in events)
    assert 'Salários' not in str([e.details for e in events])
    assert 'gera_cor' in events[-1].details['fields']


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Administrador', 'Contador', 'Operador', 'Consulta'])
async def test_chart_account_permissions(client, accounts, admin_db, role):
    auth = headers(accounts, role)
    row = ChartAccount(company_id=accounts[1][0].id, conta='00123', descricao='Visível')
    private = ChartAccount(company_id=accounts[1][1].id, conta='999', descricao='Privado')
    admin_db.add_all([row, private])
    admin_db.commit()
    async with client:
        path = endpoint(accounts)
        assert (await client.get(path, headers=auth)).status_code == 200
        assert (await client.get(endpoint(accounts, True), headers=auth)).status_code == 403
        assert (await client.get(f'{path}/{private.id}', headers=auth)).status_code == 404
        response = await client.post(path, headers=auth, json={'conta': '00234', 'descricao': 'Nova'})
        assert response.status_code == (201 if role in ('Administrador', 'Contador') else 403)
        response = await client.patch(f'{path}/{row.id}', headers=auth, json={'descricao': 'Alterada'})
        assert response.status_code == (200 if role in ('Administrador', 'Contador') else 403)
        response = await client.post(endpoint(accounts, True), headers=auth, json={'conta': '1', 'descricao': 'Negada'})
        assert response.status_code == 403
        accounts[1][0].status = 'Inativa'
        admin_db.commit()
        assert (await client.get(path, headers=auth)).status_code == 200
        response = await client.patch(f'{path}/{row.id}', headers=auth, json={'descricao': 'Inativa'})
        assert response.status_code == (409 if role in ('Administrador', 'Contador') else 403)
        accounts[0][role].is_active = False
        admin_db.commit()
        assert (await client.get(path, headers=auth)).status_code == 401


@pytest.mark.asyncio
async def test_chart_account_legacy_rows_remain_readable(client, accounts, admin_db):
    company = accounts[1][0].id
    a = ChartAccount(company_id=company, conta='00123', descricao='primeira', utiliza_cc=0, tipo_correntista='9-Nenhum', gera_cor=1)
    b = ChartAccount(company_id=company, conta='00123', descricao='segunda', utiliza_cc=1)
    empty = ChartAccount(company_id=company, conta=None, descricao=None)
    admin_db.add_all([a, b, empty])
    admin_db.flush()
    # Force literal legacy nulls instead of server defaults.
    a.tipo_correntista = None
    empty.utiliza_cc = None
    empty.gera_cor = None
    admin_db.commit()
    async with client:
        auth = headers(accounts)
        response = await client.get(endpoint(accounts) + '?conta=00123', headers=auth)
        assert response.status_code == 200
        assert [r['id'] for r in response.json()['items']] == [a.id, b.id]
        updated = await client.patch(f'{endpoint(accounts)}/{a.id}', headers=auth, json={'descricao': 'Só descrição'})
        assert updated.json()['gera_cor'] == 1
        assert updated.json()['tipo_correntista'] is None
        result = (await client.get(f'{endpoint(accounts)}/{empty.id}', headers=auth)).json()
        assert result['conta'] is None and result['utiliza_cc'] is None and result['gera_cor'] is None


@pytest.mark.asyncio
async def test_chart_account_query_is_literal_and_stable(client, accounts, admin_db):
    company = accounts[1][0].id
    admin_db.add_all([ChartAccount(company_id=company, conta=code, descricao=description) for code, description in [
        ('00123', 'Ação 100%'), ('00234', 'Conta_a'), ('00345', 'Contaxa'), ('00456', 'Ação normal')]])
    admin_db.commit()
    async with client:
        path, auth = endpoint(accounts), headers(accounts)
        for q, expected in [('%', ['00123']), ('_', ['00234']), ('ação', ['00123', '00456'])]:
            response = await client.get(path, headers=auth, params={'q': q})
            assert response.status_code == 200
            assert [r['conta'] for r in response.json()['items']] == expected
        response = (await client.get(path, headers=auth, params={'offset': 1, 'limit': 2})).json()
        assert response['total'] == 4 and [r['conta'] for r in response['items']] == ['00234', '00345']
        response = (await client.get(path, headers=auth, params={'offset': 99})).json()
        assert response['total'] == 4 and response['items'] == []
        for query in ({'limit': 0}, {'limit': 101}, {'offset': -1}):
            assert (await client.get(path, headers=auth, params=query)).status_code == 422


@pytest.mark.asyncio
async def test_chart_account_invalid_changes_do_not_write(client, accounts, admin_db):
    async with client:
        path, auth = endpoint(accounts), headers(accounts, 'Contador')
        for payload in [
            {'conta': 'abc', 'descricao': 'Inválida'}, {'conta': '1', 'descricao': ' '},
            *[{'conta': '1', 'descricao': 'Inválida', 'utiliza_cc': flag} for flag in (-1, 2, True)],
            {'conta': '1', 'descricao': 'Inválida', 'company_id': 999},
        ]:
            assert (await client.post(path, headers=auth, json=payload)).status_code == 422
        made = await client.post(path, headers=auth, json={'conta': '00123', 'descricao': 'Válida'})
        assert made.status_code == 201
        row = made.json()
        assert row['conta'] == '00123'
        assert (await client.post(path, headers=auth, json={'conta': '00123', 'descricao': 'Duplicada'})).status_code == 409
        for payload in ({}, {'conta': '00234'}, {'descricao': None}, {'utiliza_cc': True}, {'gera_cor': 1}, {'company_id': 3}):
            assert (await client.patch(f'{path}/{row["id"]}', headers=auth, json=payload)).status_code == 422
        assert (await client.get(path, headers=auth)).json()['total'] == 1


@pytest.mark.asyncio
async def test_chart_account_audit_failure_rolls_back(client, accounts, admin_db, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('audit unavailable')
    monkeypatch.setattr('app.services.companies.write_audit', fail)
    async with client:
        with pytest.raises(RuntimeError, match='audit unavailable'):
            await client.post(endpoint(accounts), headers=headers(accounts), json={'conta': '1', 'descricao': 'Rollback'})
    assert admin_db.scalar(select(ChartAccount.id)) is None
