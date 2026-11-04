from datetime import datetime, timezone
from threading import Thread
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from psycopg.errors import ExclusionViolation
from sqlalchemy import create_engine, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.user import RefreshToken, User
from tests.db import database_url, migrate

PASSWORD = 'test-only-password-123!'
START = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)
MID = datetime(2026, 11, 4, 12, 30, tzinfo=timezone.utc)
END = datetime(2026, 11, 4, 13, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 11, 4, 14, 0, tzinfo=timezone.utc)


def _user(name: str, *, admin: bool) -> User:
    suffix = uuid4().hex[:8]
    return User(
        name=name, email=f'{name}-{suffix}@agenda.test'.lower(), password_hash=hash_password(PASSWORD),
        is_admin=admin, is_active=True,
    )


@pytest.fixture
async def client(agenda_db):
    admin = _user('Admin', admin=True)
    member = _user('Ana', admin=False)
    agenda_db.add_all([admin, member])
    agenda_db.commit()

    def override_db():
        yield agenda_db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as http:
            yield http, admin, member
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


async def login(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post('/api/v1/auth/login', json={'email': email, 'password': PASSWORD})
    assert response.status_code == 200, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def reservation(room_id: int, **times) -> dict:
    payload = {'room_id': room_id, 'title': 'Planejamento', 'starts_at': START.isoformat(), 'ends_at': END.isoformat()}
    payload.update(times)
    return payload


async def test_anonymous_requests_are_rejected(client):
    http, _admin, _member = client
    assert (await http.get('/api/v1/rooms')).status_code == 401
    assert (await http.get('/api/v1/reservations', params={'from': START.isoformat(), 'to': LATER.isoformat()})).status_code == 401


async def test_new_user_must_change_password_before_using_the_agenda(client):
    http, admin, _member = client
    admin_headers = await login(http, admin.email)
    created = await http.post('/api/v1/users', json={
        'name': 'Marina', 'email': 'marina@agenda.test', 'password': 'senha-inicial-123',
    }, headers=admin_headers)
    assert created.status_code == 201, created.text
    assert created.json()['must_change_password'] is True
    login_response = await http.post('/api/v1/auth/login', json={
        'email': 'marina@agenda.test', 'password': 'senha-inicial-123',
    })
    assert login_response.status_code == 200, login_response.text
    headers = {'Authorization': f"Bearer {login_response.json()['access_token']}"}
    blocked = await http.get('/api/v1/rooms', headers=headers)
    assert blocked.status_code == 403
    assert blocked.json()['detail'] == 'Altere a senha antes de continuar.'
    profile = await http.get('/api/v1/auth/me', headers=headers)
    assert profile.status_code == 200
    assert profile.json()['must_change_password'] is True
    same = await http.post('/api/v1/auth/password', json={
        'current_password': 'senha-inicial-123', 'new_password': 'senha-inicial-123',
    }, headers=headers)
    assert same.status_code == 422
    wrong = await http.post('/api/v1/auth/password', json={
        'current_password': 'senha-errada', 'new_password': 'senha-nova-456',
    }, headers=headers)
    assert wrong.status_code == 422
    assert wrong.json()['detail'] == 'Senha atual não confere.'
    changed = await http.post('/api/v1/auth/password', json={
        'current_password': 'senha-inicial-123', 'new_password': 'senha-nova-456',
    }, headers=headers)
    assert changed.status_code == 200, changed.text
    assert changed.json()['must_change_password'] is False
    assert (await http.get('/api/v1/rooms', headers=headers)).status_code == 200


async def test_admin_can_require_password_change_on_next_access(client):
    http, admin, member = client
    admin_headers = await login(http, admin.email)
    member_login = await http.post('/api/v1/auth/login', json={'email': member.email, 'password': PASSWORD})
    assert member_login.status_code == 200
    required = await http.post(f'/api/v1/users/{member.id}/require-password-change', headers=admin_headers)
    assert required.status_code == 200, required.text
    assert required.json()['must_change_password'] is True
    refresh = await http.post('/api/v1/auth/refresh')
    assert refresh.status_code == 401
    denied = await http.post(f'/api/v1/users/{member.id}/require-password-change', headers={
        'Authorization': f"Bearer {member_login.json()['access_token']}",
    })
    assert denied.status_code == 403


async def test_member_cannot_manage_rooms_or_users(client):
    http, _admin, member = client
    headers = await login(http, member.email)
    created = await http.post('/api/v1/rooms', json={'name': 'Sala Verde', 'capacity': 8}, headers=headers)
    assert created.status_code == 403
    users = await http.post('/api/v1/users', json={
        'name': 'Novo', 'email': 'novo@agenda.test', 'password': PASSWORD,
    }, headers=headers)
    assert users.status_code == 403


async def test_admin_creates_room_and_member_books_without_overlap(client):
    http, admin, member = client
    admin_headers = await login(http, admin.email)
    room = await http.post('/api/v1/rooms', json={
        'name': 'Sala Verde', 'location': '1º andar', 'capacity': 8,
    }, headers=admin_headers)
    assert room.status_code == 201, room.text
    room_id = room.json()['id']
    member_headers = await login(http, member.email)
    listed = await http.get('/api/v1/rooms', headers=member_headers)
    assert listed.status_code == 200
    assert listed.json()[0]['name'] == 'Sala Verde'
    first = await http.post('/api/v1/reservations', json=reservation(room_id), headers=member_headers)
    assert first.status_code == 201, first.text
    adjacent = await http.post('/api/v1/reservations', json=reservation(
        room_id, starts_at=END.isoformat(), ends_at=LATER.isoformat(), title='Em seguida',
    ), headers=member_headers)
    assert adjacent.status_code == 201, adjacent.text
    overlap = await http.post('/api/v1/reservations', json=reservation(
        room_id, starts_at=MID.isoformat(), ends_at=LATER.isoformat(),
    ), headers=member_headers)
    assert overlap.status_code == 409
    assert overlap.json()['detail'] == 'Esta sala já está reservada nesse horário.'
    agenda = await http.get('/api/v1/reservations', params={
        'from': START.isoformat(), 'to': LATER.isoformat(), 'room_id': room_id,
    }, headers=member_headers)
    assert agenda.status_code == 200
    titles = [item['title'] for item in agenda.json()]
    assert titles == ['Planejamento', 'Em seguida']
    assert agenda.json()[0]['mine'] is True


async def test_member_cannot_cancel_someone_elses_reservation(client):
    http, admin, member = client
    admin_headers = await login(http, admin.email)
    room = await http.post('/api/v1/rooms', json={'name': 'Sala Azul', 'capacity': 4}, headers=admin_headers)
    room_id = room.json()['id']
    created = await http.post('/api/v1/reservations', json=reservation(room_id, title='Diretoria'), headers=admin_headers)
    reservation_id = created.json()['id']
    member_headers = await login(http, member.email)
    denied = await http.delete(f'/api/v1/reservations/{reservation_id}', headers=member_headers)
    assert denied.status_code == 403
    removed = await http.delete(f'/api/v1/reservations/{reservation_id}', headers=admin_headers)
    assert removed.status_code == 204


async def test_inactive_room_cannot_be_booked(client):
    http, admin, member = client
    admin_headers = await login(http, admin.email)
    room = await http.post('/api/v1/rooms', json={'name': 'Sala Arquivo', 'capacity': 2, 'is_active': False}, headers=admin_headers)
    member_headers = await login(http, member.email)
    hidden = await http.get('/api/v1/rooms', headers=member_headers)
    assert hidden.json() == []
    booked = await http.post('/api/v1/reservations', json=reservation(room.json()['id']), headers=member_headers)
    assert booked.status_code == 422
    assert booked.json()['detail'] == 'Sala indisponível'


def test_concurrent_overlapping_inserts_allow_only_one():
    url = database_url()
    migrate(url)
    engine = create_engine(url, connect_args={'options': '-c lock_timeout=10000 -c statement_timeout=15000'})
    suffix = uuid4().hex[:8]
    user_id = room_id = None
    try:
        with Session(engine) as db:
            user = User(name='Corrida', email=f'race-{suffix}@agenda.test', password_hash=hash_password(PASSWORD), is_admin=False, is_active=True)
            room = Room(name=f'Sala Corrida {suffix}', location='', capacity=2, is_active=True)
            db.add_all([user, room])
            db.commit()
            user_id, room_id = user.id, room.id

        results: list[str] = []

        def attempt() -> None:
            with Session(engine) as db:
                db.add(Reservation(
                    room_id=room_id, user_id=user_id, title='Ao mesmo tempo', starts_at=START, ends_at=END,
                ))
                try:
                    db.commit()
                except IntegrityError as exc:
                    db.rollback()
                    assert isinstance(exc.orig, ExclusionViolation)
                    results.append('conflict')
                else:
                    results.append('ok')

        threads = [Thread(target=attempt), Thread(target=attempt)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        assert sorted(results) == ['conflict', 'ok']
    finally:
        with engine.begin() as connection:
            if room_id is not None:
                connection.execute(delete(Reservation).where(Reservation.room_id == room_id))
                connection.execute(delete(Room).where(Room.id == room_id))
            if user_id is not None:
                connection.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
                connection.execute(delete(User).where(User.id == user_id))
        engine.dispose()
