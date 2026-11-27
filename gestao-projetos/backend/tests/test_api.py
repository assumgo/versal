from datetime import date, timedelta


TODAY = date(2026, 11, 27)


def _project(auth_headers, client, **overrides):
    headers, user = auth_headers
    payload = {
        'name': 'Rack da sala',
        'owner_id': user['id'],
        'due_date': '2026-12-20',
        'template_key': None,
        'status': 'em_andamento',
    }
    payload.update(overrides)
    response = client.post('/api/projects', json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_login_and_templates(client, auth):
    headers, user = auth
    assert user['name'] == 'Ana Lima'
    assert client.get('/api/projects', headers=headers).status_code == 200
    assert client.get('/api/projects').status_code == 401
    bad = client.post('/api/auth/login', json={'email': 'ana@example.com', 'password': 'errada'})
    assert bad.status_code == 401
    templates = client.get('/api/templates', headers=headers).json()
    by_key = {item['key']: item for item in templates}
    assert [phase['name'] for phase in by_key['rack']['phases']] == [
        'Levantamento', 'Materiais', 'Montagem', 'Testes', 'Entrega',
    ]
    assert [phase['name'] for phase in by_key['system']['phases']] == [
        'Descoberta', 'Desenho', 'Construção', 'Homologação', 'Implantação',
    ]
    assert by_key['rack']['phases'][0]['tasks'] == ['Conferir local e medidas']


def test_rack_template_copies_phases_in_order_and_stays_independent(client, auth):
    headers, _user = auth
    project = _project(auth, client, name='Rack 01', template_key='rack')
    assert [phase['name'] for phase in project['phases']] == [
        'Levantamento', 'Materiais', 'Montagem', 'Testes', 'Entrega',
    ]
    first = project['phases'][0]
    renamed = client.put(f"/api/phases/{first['id']}", json={
        'name': 'Levantamento do local',
        'status': 'em_andamento',
        'start_date': None,
        'due_date': None,
    }, headers=headers)
    assert renamed.status_code == 200
    template = next(item for item in client.get('/api/templates', headers=headers).json() if item['key'] == 'rack')
    assert template['phases'][0]['name'] == 'Levantamento'


def test_blank_project_phase_and_weighted_progress(client, auth):
    headers, user = auth
    project = _project(auth, client, name='Sistema interno', template_key=None)
    assert project['phases'] == []
    assert project['project_progress'] == 0
    phase = client.post(f"/api/projects/{project['project_id']}/phases", json={'name': 'Descoberta'}, headers=headers).json()
    second = client.post(f"/api/projects/{project['project_id']}/phases", json={'name': 'Construção'}, headers=headers).json()
    client.post(f"/api/phases/{phase['id']}/tasks", json={'title': 'Uma tarefa'}, headers=headers)
    for title in ('A', 'B', 'C'):
        client.post(f"/api/phases/{second['id']}/tasks", json={'title': title}, headers=headers)
    tasks = client.get(f"/api/phases/{phase['id']}", headers=headers).json()['tasks']
    saved = client.put(f"/api/tasks/{tasks[0]['id']}", json={
        'title': 'Uma tarefa',
        'description': '',
        'status': 'concluida',
        'assignee_id': user['id'],
        'due_date': None,
        'blocked_reason': None,
    }, headers=headers)
    assert saved.status_code == 200, saved.text
    detail = client.get(f"/api/projects/{project['project_id']}", headers=headers).json()
    by_name = {item['name']: item for item in detail['phases']}
    assert by_name['Descoberta']['progress'] == 100
    assert by_name['Construção']['progress'] == 0
    assert detail['project_progress'] == 25
    assert detail['done_tasks'] == 1
    assert detail['total_tasks'] == 4


def test_overdue_blocked_attention_window_and_portfolio_filters(client, auth):
    headers, user = auth
    late = _project(auth, client, name='Atrasado', template_key='rack', due_date='2026-12-20')
    task_id = client.get(f"/api/phases/{late['phases'][0]['id']}", headers=headers).json()['tasks'][0]['id']
    updated = client.put(f'/api/tasks/{task_id}', json={
        'title': 'Conferir local e medidas',
        'description': '',
        'status': 'a_fazer',
        'assignee_id': None,
        'due_date': '2026-11-20',
        'blocked_reason': None,
    }, headers=headers)
    assert updated.json()['overdue'] is True
    listed = client.get('/api/projects', headers=headers).json()
    row = next(item for item in listed['projects'] if item['name'] == 'Atrasado')
    assert row['health'] == 'atrasado'
    assert row['next_overdue_on'] == '2026-11-20'
    assert listed['summary']['atrasados'] == 1

    blocked = _project(auth, client, name='Bloqueado', due_date='2026-12-20')
    phase = client.post(f"/api/projects/{blocked['project_id']}/phases", json={'name': 'Fase'}, headers=headers).json()
    created = client.post(f"/api/phases/{phase['id']}/tasks", json={'title': 'Esperar peça'}, headers=headers).json()
    missing_reason = client.put(f"/api/tasks/{created['id']}", json={
        'title': 'Esperar peça', 'description': '', 'status': 'bloqueada',
        'assignee_id': None, 'due_date': None, 'blocked_reason': '  ',
    }, headers=headers)
    assert missing_reason.status_code == 422
    blocked_task = client.put(f"/api/tasks/{created['id']}", json={
        'title': 'Esperar peça', 'description': '', 'status': 'bloqueada',
        'assignee_id': user['id'], 'due_date': '2026-12-01', 'blocked_reason': 'Peça em falta',
    }, headers=headers).json()
    assert blocked_task['project_health'] == 'atencao'
    events = {event['event_type'] for event in blocked_task['events']}
    assert {'task_created', 'task_status_changed', 'task_assignee_changed', 'task_due_date_changed'} <= events

    soon = _project(auth, client, name='Janela', due_date='2026-12-30')
    horizon = (TODAY + timedelta(days=7)).isoformat()
    after = (TODAY + timedelta(days=8)).isoformat()
    soon_phase = client.post(f"/api/projects/{soon['project_id']}/phases", json={
        'name': 'Prazo curto', 'due_date': horizon,
    }, headers=headers).json()
    client.post(f"/api/phases/{soon_phase['id']}/tasks", json={'title': 'Aberta'}, headers=headers)
    assert client.get(f"/api/projects/{soon['project_id']}", headers=headers).json()['project_health'] == 'atencao'
    client.put(f"/api/phases/{soon_phase['id']}", json={
        'name': 'Prazo curto', 'status': 'em_andamento', 'start_date': None, 'due_date': after,
    }, headers=headers)
    assert client.get(f"/api/projects/{soon['project_id']}", headers=headers).json()['project_health'] == 'no_prazo'

    paused = client.post(f"/api/projects/{late['project_id']}/status", json={'status': 'pausado'}, headers=headers).json()
    assert paused['project_health'] == 'pausado'
    summary = client.get('/api/projects', headers=headers).json()['summary']
    assert summary['atrasados'] == 0
    assert summary['atencao'] == 1
    filtered = client.get('/api/projects', params={'health': 'atencao', 'q': 'blo'}, headers=headers).json()
    assert [item['name'] for item in filtered['projects']] == ['Bloqueado']
    assert client.get('/api/projects', params={'owner_id': user['id'], 'status': 'pausado'}, headers=headers).json()['projects'][0]['name'] == 'Atrasado'


def test_conflicts_reorder_lifecycle_and_draft_delete(client, auth):
    headers, user = auth
    project = _project(auth, client, name='Conflito', template_key='rack', due_date='2026-12-10')
    phase_ids = [phase['id'] for phase in project['phases']]
    task = client.get(f'/api/phases/{phase_ids[0]}', headers=headers).json()['tasks'][0]
    client.put(f"/api/tasks/{task['id']}", json={
        'title': task['title'], 'description': '', 'status': 'a_fazer',
        'assignee_id': None, 'due_date': '2026-12-15', 'blocked_reason': None,
    }, headers=headers)
    detail = client.get(f"/api/projects/{project['project_id']}", headers=headers).json()
    assert detail['schedule_conflicts'][0]['due_date'] == '2026-12-15'
    assert detail['schedule_conflicts'][0]['phase_name'] == 'Levantamento'

    reordered = client.post(f"/api/projects/{project['project_id']}/phases/reorder", json={
        'ids': list(reversed(phase_ids)),
    }, headers=headers).json()
    assert [phase['name'] for phase in reordered['phases']][0] == 'Entrega'
    bad_order = client.post(f"/api/projects/{project['project_id']}/phases/reorder", json={'ids': phase_ids[:2]}, headers=headers)
    assert bad_order.status_code == 422

    tasks = client.get(f'/api/phases/{phase_ids[1]}', headers=headers).json()['tasks']
    moved = client.post(f'/api/phases/{phase_ids[1]}/tasks/reorder', json={'ids': [task['id'] for task in tasks]}, headers=headers)
    assert moved.status_code == 200

    open_count = sum(phase['total_tasks'] - phase['done_tasks'] for phase in detail['phases'])
    refused = client.post(f"/api/projects/{project['project_id']}/status", json={'status': 'concluido'}, headers=headers)
    assert refused.status_code == 409
    assert refused.json()['detail']['open_task_count'] == open_count
    confirmed = client.post(f"/api/projects/{project['project_id']}/status", json={
        'status': 'concluido', 'confirm_open_tasks': True,
    }, headers=headers)
    assert confirmed.status_code == 200
    assert confirmed.json()['project_status'] == 'concluido'
    assert client.delete(f"/api/projects/{project['project_id']}", headers=headers).status_code == 409

    draft = _project(auth, client, name='Rascunho', status='rascunho', template_key=None)
    phase = client.post(f"/api/projects/{draft['project_id']}/phases", json={'name': 'Só uma'}, headers=headers).json()
    client.put(f"/api/phases/{phase['id']}", json={
        'name': 'Só uma', 'status': 'concluida', 'start_date': None, 'due_date': None,
    }, headers=headers)
    assert client.get(f"/api/phases/{phase['id']}", headers=headers).json()['progress'] == 100
    assert client.delete(f"/api/projects/{draft['project_id']}", headers=headers).status_code == 204
    assert client.get(f"/api/projects/{draft['project_id']}", headers=headers).status_code == 404

    overdue_filter = client.get(f"/api/projects/{project['project_id']}/tasks", params={'filtro': 'atrasadas'}, headers=headers)
    assert overdue_filter.status_code == 200
    assert client.post('/api/users', json={
        'name': 'Bruno Dias', 'email': 'bruno@example.com', 'password': 'senha-segura',
    }, headers=headers).status_code == 201
    duplicate = client.post('/api/users', json={
        'name': 'Outra Ana', 'email': 'ana@example.com', 'password': 'senha-segura',
    }, headers=headers)
    assert duplicate.status_code == 409
    assert user['id']
