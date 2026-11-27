from datetime import date

from app.services.health import next_overdue_on, progress_percent, project_health, task_is_overdue

TODAY = date(2026, 11, 27)


def test_progress_weights_tasks_and_stays_below_100_while_open():
    assert progress_percent(1, 4) == 25
    assert progress_percent(1, 3) == 33
    assert progress_percent(2, 3) == 66
    assert progress_percent(3, 3) == 100
    assert progress_percent(0, 0) == 0
    assert progress_percent(0, 0, empty_is_complete=True) == 100


def test_overdue_beats_attention_and_closed_status_wins():
    assert project_health(
        status='em_andamento', due_date=date(2026, 12, 1), overdue_tasks=1,
        blocked_tasks=2, phase_attention=True, today=TODAY,
    ) == 'atrasado'
    assert project_health(
        status='em_andamento', due_date=date(2026, 11, 26), overdue_tasks=0,
        blocked_tasks=0, phase_attention=False, today=TODAY,
    ) == 'atrasado'
    assert project_health(
        status='pausado', due_date=date(2026, 11, 1), overdue_tasks=4,
        blocked_tasks=1, phase_attention=True, today=TODAY,
    ) == 'pausado'
    assert project_health(
        status='concluido', due_date=None, overdue_tasks=0,
        blocked_tasks=0, phase_attention=False, today=TODAY,
    ) == 'concluido'


def test_attention_and_on_track():
    assert project_health(
        status='rascunho', due_date=date(2026, 12, 20), overdue_tasks=0,
        blocked_tasks=1, phase_attention=False, today=TODAY,
    ) == 'atencao'
    assert project_health(
        status='em_andamento', due_date=date(2026, 12, 20), overdue_tasks=0,
        blocked_tasks=0, phase_attention=True, today=TODAY,
    ) == 'atencao'
    assert project_health(
        status='em_andamento', due_date=TODAY, overdue_tasks=0,
        blocked_tasks=0, phase_attention=False, today=TODAY,
    ) == 'no_prazo'


def test_task_overdue_ignores_done_and_missing_dates():
    assert task_is_overdue(date(2026, 11, 26), 'a_fazer', TODAY)
    assert not task_is_overdue(date(2026, 11, 26), 'concluida', TODAY)
    assert not task_is_overdue(TODAY, 'a_fazer', TODAY)
    assert not task_is_overdue(None, 'a_fazer', TODAY)


def test_next_overdue_date_is_the_earliest_open_deadline():
    assert next_overdue_on(
        status='em_andamento', due_date=date(2026, 11, 20),
        earliest_task_due=date(2026, 11, 25), today=TODAY, health='atrasado',
    ) == date(2026, 11, 20)
    assert next_overdue_on(
        status='pausado', due_date=date(2026, 11, 1),
        earliest_task_due=date(2026, 11, 1), today=TODAY, health='pausado',
    ) is None
