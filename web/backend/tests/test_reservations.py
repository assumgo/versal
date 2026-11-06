from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from test_authorization import accounts, admin_db, client, headers
from app.models.appointment import Appointment
from app.models.audit import AuditLog
from app.services import reservations

ZONE = ZoneInfo('America/Sao_Paulo')
PATH = '/api/v1/reservations'


def freeze(monkeypatch, moment: datetime) -> None:
    monkeypatch.setattr(reservations, 'now_local', lambda: moment)


def payload(**changes):
    return {'scheduled_date': '2026-10-15', 'starts_at': '09:30', 'ends_at': '10:30',
            'title': '  Reunião da sala  ', 'details': '  Projetor  ', **changes}


@pytest.mark.asyncio
async def test_room_reservations_ignore_payroll_appointments(client, accounts, admin_db, monkeypatch):
    freeze(monkeypatch, datetime(2026, 10, 15, 8, 0, tzinfo=ZONE))
    admin_db.add(Appointment(company_id=accounts[1][0].id, scheduled_date=datetime(2026, 10, 15).date(),
                             starts_at=datetime(2026, 10, 15, 9, 0).time(), ends_at=datetime(2026, 10, 15, 10, 0).time(),
                             title='Folha'))
    admin_db.commit()
    async with client:
        created = await client.post(PATH, headers=headers(accounts), json=payload())
        assert created.status_code == 201, created.text
        assert created.json()['title'] == 'Reunião da sala'
        assert created.json()['details'] == 'Projetor'
        assert created.json()['action'] == 'Agendada'
        assert 'company_id' not in created.json()
        listed = await client.get(f'{PATH}?month=2026-10', headers=headers(accounts, 'Consulta'))
        assert listed.status_code == 200
        assert [row['title'] for row in listed.json()] == ['Reunião da sala']
    event = admin_db.scalar(select(AuditLog).where(AuditLog.action == 'reservation.create'))
    assert event.company_id is None
    assert 'Reunião' not in str(event.details)


@pytest.mark.asyncio
@pytest.mark.parametrize('role,status', [('Administrador', 201), ('Contador', 201), ('Operador', 201), ('Consulta', 403)])
async def test_room_reservation_write_roles(client, accounts, monkeypatch, role, status):
    freeze(monkeypatch, datetime(2026, 10, 15, 8, 0, tzinfo=ZONE))
    async with client:
        response = await client.post(PATH, headers=headers(accounts, role), json=payload())
    assert response.status_code == status


@pytest.mark.asyncio
@pytest.mark.parametrize('changes,detail', [
    ({'ends_at': '09:30'}, 'depois do início'),
    ({'starts_at': '09:00', 'ends_at': '11:01'}, '2 horas'),
    ({'starts_at': '08:20', 'ends_at': '09:20'}, '30 minutos'),
    ({'scheduled_date': '2026-10-14', 'starts_at': '18:00', 'ends_at': '19:00'}, '30 minutos'),
])
async def test_room_reservation_time_rules(client, accounts, admin_db, monkeypatch, changes, detail):
    freeze(monkeypatch, datetime(2026, 10, 15, 8, 0, tzinfo=ZONE))
    async with client:
        response = await client.post(PATH, headers=headers(accounts), json=payload(**changes))
    assert response.status_code == 422
    assert detail in response.text
    assert admin_db.scalars(select(Appointment).where(Appointment.company_id.is_(None))).all() == []


@pytest.mark.asyncio
async def test_two_hours_is_allowed_and_finished_after_the_end(client, accounts, monkeypatch):
    moment = datetime(2026, 10, 15, 8, 0, tzinfo=ZONE)
    freeze(monkeypatch, moment)
    async with client:
        created = await client.post(PATH, headers=headers(accounts), json=payload(starts_at='09:00', ends_at='11:00'))
        assert created.status_code == 201, created.text
        assert created.json()['action'] == 'Agendada'
        freeze(monkeypatch, datetime(2026, 10, 15, 11, 0, tzinfo=ZONE))
        listed = await client.get(f'{PATH}?month=2026-10', headers=headers(accounts, 'Consulta'))
    assert listed.json()[0]['action'] == 'Finalizado'
