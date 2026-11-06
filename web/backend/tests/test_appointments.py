from datetime import date, time

import pytest
from sqlalchemy import select

from test_authorization import COMPANIES, accounts, admin_db, client, headers
from app.models.appointment import Appointment
from app.models.audit import AuditLog


def endpoint(accounts, private=False):
    return f'{COMPANIES}/{accounts[1][int(private)].id}/appointments'


def payload(**changes):
    return {'scheduled_date': '2026-10-15', 'starts_at': '09:30', 'title': 'Fechamento da folha',
            'details': 'Levar os recibos.', **changes}


@pytest.mark.asyncio
async def test_month_lists_only_the_company_schedule_in_order(client, accounts, admin_db):
    company_id = accounts[1][0].id
    admin_db.add_all([
        Appointment(company_id=company_id, scheduled_date=date(2026, 10, 15), starts_at=time(14, 0), ends_at=time(15, 0), title='Tarde'),
        Appointment(company_id=company_id, scheduled_date=date(2026, 10, 15), starts_at=time(9, 0), ends_at=time(10, 0), title='Manhã'),
        Appointment(company_id=company_id, scheduled_date=date(2026, 11, 1), starts_at=time(8, 0), ends_at=time(9, 0), title='Outro mês'),
        Appointment(company_id=accounts[1][1].id, scheduled_date=date(2026, 10, 15), starts_at=time(9, 0), ends_at=time(10, 0), title='Outra empresa'),
    ])
    admin_db.commit()
    async with client:
        listed = await client.get(f'{endpoint(accounts)}?month=2026-10', headers=headers(accounts, 'Consulta'))
        assert listed.status_code == 200, listed.text
        assert [(row['title'], row['starts_at']) for row in listed.json()] == [('Manhã', '09:00'), ('Tarde', '14:00')]
        hidden = await client.get(f'{endpoint(accounts, True)}?month=2026-10', headers=headers(accounts, 'Consulta'))
        assert hidden.status_code == 403
        assert (await client.get(endpoint(accounts), headers=headers(accounts))).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize('role,status', [
    ('Administrador', 201), ('Contador', 201), ('Operador', 201), ('Consulta', 403),
])
async def test_schedule_permissions_audit_and_inactive_company(client, accounts, admin_db, role, status):
    path = endpoint(accounts)
    async with client:
        created = await client.post(path, headers=headers(accounts, role), json=payload(title='  Reunião  ', details='  '))
        assert created.status_code == status, created.text
        if status == 201:
            assert created.json()['title'] == 'Reunião'
            assert created.json()['details'] is None
            assert created.json()['scheduled_date'] == '2026-10-15'
            company = accounts[1][0]
            company.status = 'Inativa'
            admin_db.commit()
            blocked = await client.post(path, headers=headers(accounts, role), json=payload(title='Depois'))
            assert blocked.status_code == 409
            assert (await client.get(f'{path}?month=2026-10', headers=headers(accounts, 'Consulta'))).status_code == 200
        if status == 403:
            assert admin_db.scalars(select(Appointment)).all() == []
            return
        event = admin_db.scalar(select(AuditLog))
        assert event.action == 'appointment.create'
        assert event.actor_id == accounts[0][role].id
        assert 'Reunião' not in str(event.details)


@pytest.mark.asyncio
@pytest.mark.parametrize('changes', [
    {'title': '   '}, {'title': 'x' * 121}, {'starts_at': '25:00'}, {'scheduled_date': '2026-13-01'},
    {'details': 'x' * 501}, {'company_id': 1},
])
async def test_invalid_appointment_is_rejected(client, accounts, admin_db, changes):
    async with client:
        response = await client.post(endpoint(accounts), headers=headers(accounts), json=payload(**changes))
    assert response.status_code == 422
    assert admin_db.scalars(select(Appointment)).all() == []
