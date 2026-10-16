import pytest
from sqlalchemy import select

from test_authorization import admin_db, accounts, client, headers, COMPANIES
from app.models import ChartAccount, Rubric
from app.models.audit import AuditLog

FLAGS = ('debito_gera_cc', 'debito_gera_cor', 'credito_gera_cc', 'credito_gera_cor')


def endpoint(accounts, private=False):
    return f'{COMPANIES}/{accounts[1][int(private)].id}/rubrics'


@pytest.mark.asyncio
async def test_rubric_save_uses_plan_flags(client, accounts, admin_db):
    company = accounts[1][0].id
    admin_db.add_all([
        ChartAccount(company_id=company, conta='001', utiliza_cc=0, gera_cor=0),
        ChartAccount(company_id=company, conta='002', utiliza_cc=1, gera_cor=1),
        ChartAccount(company_id=accounts[1][1].id, conta='003', utiliza_cc=0, gera_cor=0),
    ])
    admin_db.commit()
    async with client:
        path, auth = endpoint(accounts), headers(accounts, 'Contador')
        for code, manual, expected in [('001', 1, 0), ('002', 0, 1), ('003', 1, 1), ('999', 0, 0)]:
            response = await client.post(path, headers=auth, json={
                'codigo': code, 'descricao': 'Regra', 'conta_debito': code, 'conta_credito': code,
                **{flag: manual for flag in FLAGS},
            })
            assert response.status_code == 201, response.text
            assert [response.json()[key] for key in FLAGS] == [expected] * 4
        row = admin_db.scalar(select(Rubric).where(Rubric.company_id == company, Rubric.codigo == '001'))
        for flag in FLAGS:
            setattr(row, flag, 1)
        admin_db.commit()
        # GET never synchronizes stored divergences.
        result = (await client.get(f'{path}/{row.id}', headers=auth)).json()
        assert [result[key] for key in FLAGS] == [1] * 4
        for change in ({'descricao': 'Só descrição'}, {'status': 'Inativa'}):
            for flag in FLAGS:
                setattr(row, flag, 1)
            admin_db.commit()
            response = await client.patch(f'{path}/{row.id}', headers=auth, json=change)
            assert response.status_code == 200
            assert [response.json()[key] for key in FLAGS] == [0] * 4
        assert admin_db.get(Rubric, row.id) is not None
        assert (await client.delete(f'{path}/{row.id}', headers=auth)).status_code == 405


@pytest.mark.asyncio
async def test_rubric_defaults_history_and_partial_legacy_updates(client, accounts, admin_db):
    async with client:
        path, auth = endpoint(accounts), headers(accounts)
        response = await client.post(path, headers=auth, json={'codigo': 'FGTS', 'descricao': ' Encargo ', 'tipo': 'E'})
        assert response.status_code == 201, response.text
        row = response.json()
        assert row['descricao'] == 'Encargo'
        assert row['historico_id'] == '001000182'
        assert [row[key] for key in FLAGS] == [1] * 4
        for value, expected in [('182', '000000182'), ('1000182', '001000182'), ('123456789012', '456789012'), ('', '001000182')]:
            result = await client.patch(f'{path}/{row["id"]}', headers=auth, json={'historico_id': value})
            assert result.status_code == 200
            assert result.json()['historico_id'] == expected
        legacy = admin_db.get(Rubric, row['id'])
        legacy.historico = 'h' * 250
        legacy.tipo = 'LEGADO'
        legacy.historico_id = None
        legacy.debito_gera_cc = None
        admin_db.commit()
        result = (await client.patch(f'{path}/{row["id"]}', headers=auth, json={'descricao': 'Atualizada'})).json()
        assert result['historico'] == 'h' * 250 and result['tipo'] == 'LEGADO'
        assert result['historico_id'] is None and result['debito_gera_cc'] is None
        result = (await client.patch(f'{path}/{row["id"]}', headers=auth, json={'historico': ' ' + 'x' * 220 + ' '})).json()
        assert result['historico'] == 'x' * 200
        assert (await client.post(path, headers=auth, json={'codigo': 'FGTS', 'descricao': 'Duplicada'})).status_code == 409
        for payload in ({}, {'codigo': ''}, {'descricao': None}, {'tipo': 'X'}, {'status': None}, {'debito_gera_cc': True}, {'company_id': 3}):
            assert (await client.patch(f'{path}/{row["id"]}', headers=auth, json=payload)).status_code == 422
        result = (await client.get(path, headers=auth, params={'status': 'Inativa'})).json()
        assert result['total'] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Administrador', 'Contador', 'Operador', 'Consulta'])
async def test_rubric_permissions(client, accounts, admin_db, role):
    row = Rubric(company_id=accounts[1][0].id, codigo='01', descricao='Visível')
    private = Rubric(company_id=accounts[1][1].id, codigo='01', descricao='Privada')
    admin_db.add_all([row, private])
    admin_db.commit()
    async with client:
        path, auth = endpoint(accounts), headers(accounts, role)
        assert (await client.get(path, headers=auth)).status_code == 200
        assert (await client.get(endpoint(accounts, True), headers=auth)).status_code == 403
        assert (await client.get(f'{path}/{private.id}', headers=auth)).status_code == 404
        allowed = role in ('Administrador', 'Contador')
        response = await client.patch(f'{path}/{row.id}', headers=auth, json={'descricao': 'Alterada'})
        assert response.status_code == (200 if allowed else 403)
        response = await client.post(path, headers=auth, json={'codigo': '02', 'descricao': 'Nova'})
        assert response.status_code == (201 if allowed else 403)
        accounts[1][0].status = 'Inativa'
        admin_db.commit()
        assert (await client.get(path, headers=auth)).status_code == 200
        response = await client.patch(f'{path}/{row.id}', headers=auth, json={'descricao': 'Negada'})
        assert response.status_code == (409 if allowed else 403)


@pytest.mark.asyncio
@pytest.mark.parametrize('flag', [None, 2])
async def test_incomplete_legacy_account_blocks_save_atomically(client, accounts, admin_db, flag):
    account = ChartAccount(company_id=accounts[1][0].id, conta='001', utiliza_cc=0, gera_cor=0)
    rubric = Rubric(company_id=accounts[1][0].id, codigo='01', descricao='Antes', conta_debito='001', debito_gera_cc=1)
    admin_db.add_all([account, rubric])
    admin_db.flush()
    account.gera_cor = flag
    admin_db.commit()
    async with client:
        result = await client.patch(f'{endpoint(accounts)}/{rubric.id}', headers=headers(accounts), json={'descricao': 'Depois'})
        assert result.status_code == 409
    admin_db.refresh(rubric)
    assert rubric.descricao == 'Antes' and rubric.debito_gera_cc == 1
    assert admin_db.scalar(select(AuditLog.id)) is None


@pytest.mark.asyncio
async def test_rubric_duplicate_lookup_and_audit_rollback(client, accounts, admin_db, monkeypatch):
    company = accounts[1][0].id
    admin_db.add_all([ChartAccount(company_id=company, conta='001', utiliza_cc=0, gera_cor=0),
                      ChartAccount(company_id=company, conta='001', utiliza_cc=1, gera_cor=1)])
    a = Rubric(company_id=company, codigo='DUP', descricao='Primeira')
    b = Rubric(company_id=company, codigo='DUP', descricao='Segunda')
    admin_db.add_all([a, b])
    admin_db.commit()
    async with client:
        path, auth = endpoint(accounts), headers(accounts)
        result = await client.patch(f'{path}/{a.id}', headers=auth, json={'codigo': 'DUP', 'conta_debito': '0.01'})
        assert result.status_code == 200 and result.json()['debito_gera_cc'] == 0
        events = admin_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
        assert 'debito_gera_cc' in events[-1].details['fields']
        assert 'Primeira' not in str(events[-1].details)
        def fail(*args, **kwargs):
            raise RuntimeError('audit failed')
        monkeypatch.setattr('app.services.companies.write_audit', fail)
        with pytest.raises(RuntimeError):
            await client.patch(f'{path}/{a.id}', headers=auth, json={'descricao': 'Não persistir'})
        assert admin_db.get(Rubric, a.id).descricao == 'Primeira'
        result = (await client.get(path, headers=auth, params={'q': 'DUP', 'limit': 1, 'offset': 1})).json()
        assert result['total'] == 2 and result['items'][0]['id'] == b.id
