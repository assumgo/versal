"""Authorization contracts exercised through HTTP against disposable PostgreSQL."""
import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.main import app
from app.models.audit import AuditLog
from app.models.company import Company
from app.models.user import Role, User, UserCompany

PASSWORD = 'test-only-password-123!'
USERS = '/api/v1/users'
COMPANIES = '/api/v1/companies'


@pytest.fixture
def admin_db():
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to disposable, migrated PostgreSQL')
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                with Session(bind=connection, join_transaction_mode='create_savepoint') as db:
                    yield db
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


@pytest.fixture
def accounts(admin_db):
    encoded = hash_password(PASSWORD)
    users = {name: User(email=f'{index}@authorization.test', password_hash=encoded,
                        role=Role(name=name), is_active=True)
             for index, name in enumerate(('Administrador', 'Contador', 'Operador', 'Consulta'))}
    companies = [Company(razao='Visible company'), Company(razao='Private company')]
    admin_db.add_all([*users.values(), *companies])
    admin_db.flush()
    admin_db.add_all(UserCompany(user_id=user.id, company_id=companies[0].id)
                     for user in users.values())
    admin_db.flush()
    # Release the fixture savepoint, keeping the outer rollback isolation.
    # Request rollback must not erase the preexisting administrator account.
    admin_db.commit()
    return users, companies


@pytest.fixture
def client(admin_db, accounts):
    def override_db():
        yield admin_db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        yield AsyncClient(transport=ASGITransport(app=app), base_url='https://test')
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def headers(accounts, role='Administrador'):
    return {'Authorization': f'Bearer {create_access_token(accounts[0][role].id)}'}


def payload(**changes):
    return {'email': 'new@authorization.test', 'password': PASSWORD,
            'role': 'Operador', **changes}


@pytest.mark.asyncio
async def test_admin_creates_user_and_grants_and_revokes_company_access(client, accounts, admin_db):
    users, companies = accounts
    async with client:
        created = await client.post(USERS, json=payload(), headers=headers(accounts))
        assert created.status_code == 201, created.text
        user_id = created.json()['id']
        saved = admin_db.get(User, user_id)
        assert verify_password(PASSWORD, saved.password_hash)
        assert created.json() == {'id': user_id, 'email': 'new@authorization.test',
                                  'role': 'Operador', 'is_active': True}
        endpoint = f'{USERS}/{user_id}/companies/{companies[1].id}'
        granted = await client.put(endpoint, headers=headers(accounts))
        assert granted.status_code == 204, granted.text
        user_headers = {'Authorization': f'Bearer {create_access_token(user_id)}'}
        visible = await client.get(f'{COMPANIES}/{companies[1].id}', headers=user_headers)
        assert visible.status_code == 200
        memberships = await client.get(f'{USERS}/{user_id}/companies', headers=headers(accounts))
        assert memberships.json() == [{'company_id': companies[1].id}]
        assert (await client.delete(endpoint, headers=headers(accounts))).status_code == 204
        assert (await client.get(f'{COMPANIES}/{companies[1].id}', headers=user_headers)).status_code == 403
    assert admin_db.scalar(select(UserCompany).where(UserCompany.user_id == user_id)) is None
    events = admin_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [event.action for event in events] == ['user.create', 'membership.grant', 'membership.revoke']
    assert all(event.actor_id == users['Administrador'].id for event in events)
    assert all(event.ip_address == '127.0.0.1' for event in events)
    assert events[1].company_id == companies[1].id
    assert PASSWORD not in str([event.details for event in events])
    assert saved.password_hash not in str([event.details for event in events])


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Administrador', 'Contador', 'Operador', 'Consulta'])
async def test_company_reads_are_scoped_even_for_admin(client, accounts, role):
    companies = accounts[1]
    async with client:
        listed = await client.get(COMPANIES, headers=headers(accounts, role))
        assert listed.status_code == 200
        assert [row['id'] for row in listed.json()] == [companies[0].id]
        assert (await client.get(f'{COMPANIES}/{companies[0].id}', headers=headers(accounts, role))).status_code == 200
        for company_id in (companies[1].id, 9223372036854775807):
            denied = await client.get(f'{COMPANIES}/{company_id}', headers=headers(accounts, role))
            assert denied.status_code == 403
            assert 'Private company' not in denied.text


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Contador', 'Operador', 'Consulta'])
async def test_non_admin_cannot_read_users_or_mutate_administration(client, accounts, admin_db, role):
    target = accounts[0]['Consulta'].id
    membership = f'{USERS}/{target}/companies/{accounts[1][1].id}'
    async with client:
        for method, path, body in [
            ('GET', USERS, None), ('GET', f'{USERS}/{target}', None),
            ('GET', f'{USERS}/{target}/companies', None),
            ('POST', USERS, payload()), ('PATCH', f'{USERS}/{target}', {'role': 'Administrador'}),
            ('DELETE', f'{USERS}/{target}', None),
            ('PUT', membership, None), ('DELETE', membership, None),
        ]:
            response = await client.request(method, path, json=body, headers=headers(accounts, role))
            assert response.status_code == 403, (method, path, response.text)
    assert admin_db.scalar(select(User).where(User.email == 'new@authorization.test')) is None
    assert accounts[0]['Consulta'].role.name == 'Consulta'
    assert accounts[0]['Consulta'].is_active
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
async def test_admin_lists_reads_updates_and_inactivates_user(client, accounts, admin_db):
    target = accounts[0]['Consulta']
    auth = headers(accounts, 'Consulta')
    async with client:
        listed = await client.get(USERS, headers=headers(accounts))
        assert listed.status_code == 200
        assert {row['id'] for row in listed.json()} == {user.id for user in accounts[0].values()}
        read = await client.get(f'{USERS}/{target.id}', headers=headers(accounts))
        assert read.json()['role'] == 'Consulta'
        changed = await client.patch(f'{USERS}/{target.id}', headers=headers(accounts), json={
            'email': 'changed@authorization.test', 'role': 'Contador', 'password': PASSWORD + 'new',
        })
        assert changed.status_code == 200, changed.text
        assert changed.json()['role'] == 'Contador'
        assert changed.json()['email'] == 'changed@authorization.test'
        assert verify_password(PASSWORD + 'new', admin_db.get(User, target.id).password_hash)
        # Role changes apply to already issued JWTs: no role is trusted from the token.
        assert (await client.get(USERS, headers=auth)).status_code == 403
        removed = await client.delete(f'{USERS}/{target.id}', headers=headers(accounts))
        assert removed.status_code == 204
        assert admin_db.get(User, target.id).is_active is False
        assert (await client.get(COMPANIES, headers=auth)).status_code == 401
    events = admin_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [event.action for event in events] == ['user.update', 'user.inactivate']
    assert PASSWORD not in str([event.details for event in events])


@pytest.mark.asyncio
@pytest.mark.parametrize('changes', [
    {'email': 'invalid'}, {'email': ''}, {'password': 'short'}, {'role': 'Unknown'},
    {'is_active': None}, {'role': None}, {'email': None}, {'password': None},
    {'company_ids': [1]}, {'password': 'sensitive-' * 200},
])
async def test_invalid_user_payloads_do_not_persist_or_echo_secrets(client, accounts, admin_db, changes):
    async with client:
        response = await client.post(USERS, json=payload(**changes), headers=headers(accounts))
    assert response.status_code == 422, response.text
    assert 'sensitive-' not in response.text
    assert admin_db.scalar(select(User).where(User.email == 'new@authorization.test')) is None
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
async def test_duplicate_email_and_membership_do_not_create_partial_changes(client, accounts, admin_db):
    target = accounts[0]['Consulta']
    async with client:
        duplicate = await client.post(USERS, json=payload(email=target.email), headers=headers(accounts))
        assert duplicate.status_code == 409
        updated = await client.patch(f'{USERS}/{target.id}', json={
            'email': accounts[0]['Operador'].email, 'role': 'Administrador',
        }, headers=headers(accounts))
        assert updated.status_code == 409
        assert admin_db.get(User, target.id).role.name == 'Consulta'
        endpoint = f'{USERS}/{target.id}/companies/{accounts[1][0].id}'
        for _ in range(2):
            assert (await client.put(endpoint, headers=headers(accounts))).status_code == 204
    assert len(admin_db.scalars(select(UserCompany).where(UserCompany.user_id == target.id)).all()) == 1
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
async def test_unknown_administration_targets_return_404_without_audit(client, accounts, admin_db):
    missing = 9223372036854775807
    async with client:
        for method, path, body in [
            ('GET', f'{USERS}/{missing}', None),
            ('PATCH', f'{USERS}/{missing}', {'role': 'Consulta'}),
            ('DELETE', f'{USERS}/{missing}', None),
            ('GET', f'{USERS}/{missing}/companies', None),
            ('PUT', f'{USERS}/{missing}/companies/{accounts[1][0].id}', None),
            ('PUT', f'{USERS}/{accounts[0]["Consulta"].id}/companies/{missing}', None),
        ]:
            response = await client.request(method, path, json=body, headers=headers(accounts))
            assert response.status_code == 404, response.text
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
async def test_administration_and_company_routes_require_authentication(client, accounts):
    async with client:
        for path in (USERS, COMPANIES, f'{COMPANIES}/{accounts[1][0].id}'):
            assert (await client.get(path)).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize('changes', [{}, {'email': None}, {'role': None}, {'password': None},
                                     {'is_active': None}, {'role': 'Unknown'}, {'email': 'invalid'},
                                     {'password': 'sensitive-' * 200}, {'company_ids': [1]}])
async def test_invalid_updates_leave_user_unchanged(client, accounts, admin_db, changes):
    target = accounts[0]['Consulta']
    async with client:
        response = await client.patch(f'{USERS}/{target.id}', json=changes, headers=headers(accounts))
    assert response.status_code == 422
    assert 'sensitive-' not in response.text
    assert admin_db.get(User, target.id).email == '3@authorization.test'
    assert admin_db.get(User, target.id).role.name == 'Consulta'
    assert admin_db.scalars(select(AuditLog)).all() == []


@pytest.mark.asyncio
async def test_role_and_membership_changes_take_effect_on_existing_access_tokens(client, accounts):
    target = accounts[0]['Operador']
    target_headers = headers(accounts, 'Operador')
    async with client:
        changed = await client.patch(f'{USERS}/{target.id}', json={'role': 'Administrador'},
                                     headers=headers(accounts))
        assert changed.status_code == 200
        assert (await client.get(USERS, headers=target_headers)).status_code == 200
        changed = await client.patch(f'{USERS}/{target.id}', json={'role': 'Consulta'},
                                     headers=headers(accounts))
        assert changed.status_code == 200
        assert (await client.get(USERS, headers=target_headers)).status_code == 403
        removed = await client.delete(f'{USERS}/{target.id}/companies/{accounts[1][0].id}',
                                      headers=headers(accounts))
        assert removed.status_code == 204
        assert (await client.get(COMPANIES, headers=target_headers)).json() == []
        assert (await client.get(f'{COMPANIES}/{accounts[1][0].id}', headers=target_headers)).status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['create', 'update', 'inactivate', 'grant', 'revoke'])
async def test_audit_failure_rolls_back_administration_changes(
    client, accounts, admin_db, monkeypatch, operation,
):
    from app.services import users

    def fail_audit(*args, **kwargs):
        raise RuntimeError('synthetic audit failure')

    monkeypatch.setattr(users, 'write_audit', fail_audit)
    target = accounts[0]['Consulta']
    target_id = target.id
    company_id = accounts[1][1 if operation == 'grant' else 0].id
    method, endpoint, body = {
        'create': ('POST', USERS, payload()),
        'update': ('PATCH', f'{USERS}/{target_id}', {'email': 'changed@authorization.test'}),
        'inactivate': ('DELETE', f'{USERS}/{target_id}', None),
        'grant': ('PUT', f'{USERS}/{target_id}/companies/{company_id}', None),
        'revoke': ('DELETE', f'{USERS}/{target_id}/companies/{company_id}', None),
    }[operation]
    async with client:
        with pytest.raises(RuntimeError, match='synthetic audit failure'):
            await client.request(method, endpoint, json=body, headers=headers(accounts))
    assert admin_db.scalar(select(User).where(User.email == 'new@authorization.test')) is None
    restored = admin_db.get(User, target_id)
    assert restored.email == '3@authorization.test'
    assert restored.is_active
    memberships = admin_db.scalars(select(UserCompany).where(UserCompany.user_id == target_id)).all()
    assert [row.company_id for row in memberships] == [accounts[1][0].id]
    assert admin_db.scalars(select(AuditLog)).all() == []
