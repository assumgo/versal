import json
from pathlib import Path

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_engine
from app.scripts.migrate_sqlite import main
from test_migration_transfer import source, target  # Shared synthetic integration fixtures.


@pytest.fixture
def configured(monkeypatch, target):
    monkeypatch.setenv('DATABASE_URL', target.url.render_as_string(hide_password=False))
    # Preserve the fixture's isolated search_path and avoid cached engines from other tests.
    get_settings.cache_clear()
    monkeypatch.setattr('app.scripts.migrate_sqlite.get_engine', lambda: target)
    yield target
    get_settings.cache_clear()
    get_engine.cache_clear()


def test_cli_defaults_to_simulation_and_writes_private_report(source, configured, tmp_path, capsys):
    report = tmp_path / 'report.json'
    assert main(['--source', str(source), '--report', str(report)]) == 0
    result = json.loads(report.read_text())
    assert result['mode'] == 'simulate'
    assert result['committed'] is False
    assert report.stat().st_mode & 0o777 == 0o600
    with configured.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM companies')) == 0
    assert 'Empresa sintética' not in report.read_text() + capsys.readouterr().out


def test_cli_apply_and_repetition_refusal(source, configured, tmp_path):
    report = tmp_path / 'report.json'
    assert main(['--source', str(source), '--apply', '--report', str(report)]) == 0
    assert json.loads(report.read_text())['committed'] is True
    assert main(['--source', str(source), '--apply']) == 1


def test_report_failure_after_commit_is_explicit(source, configured, tmp_path, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise OSError('disk full')
    monkeypatch.setattr('app.scripts.migrate_sqlite._write_report', fail)
    assert main(['--source', str(source), '--apply', '--report', str(tmp_path / 'report.json')]) == 1
    assert 'Carga confirmada; falha ao salvar relatório' in capsys.readouterr().err
    with configured.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM companies')) == 1


@pytest.mark.parametrize('destination', ['existing', 'source', 'wal', 'missing_parent', 'repository'])
def test_invalid_report_refused_before_any_database_access(source, tmp_path, destination, monkeypatch, capsys):
    paths = {
        'existing': tmp_path / 'existing.json', 'source': source,
        'wal': Path(str(source) + '-wal'), 'missing_parent': tmp_path / 'missing' / 'report.json',
        'repository': Path(__file__).parent / 'should-not-exist-report.json',
    }
    (tmp_path / 'existing.json').write_text('preserve')
    source_before = source.read_bytes()
    def forbidden():
        pytest.fail('Invalid report must be rejected before connecting')
    monkeypatch.setattr('app.scripts.migrate_sqlite.get_engine', forbidden)
    assert main(['--source', str(source), '--apply', '--report', str(paths[destination])]) == 1
    assert (tmp_path / 'existing.json').read_text() == 'preserve'
    assert source.read_bytes() == source_before
    assert not paths['repository'].exists()


def test_cli_does_not_expose_configuration_or_driver_secrets(source, monkeypatch, capsys):
    from sqlalchemy.exc import OperationalError
    secret = 'secret-password-and-personal-data'
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://example:secret@localhost/test')
    get_settings.cache_clear()
    def fail():
        raise OperationalError('INSERT private-person', {'cpf': secret}, Exception(secret))
    monkeypatch.setattr('app.scripts.migrate_sqlite.get_engine', fail)
    assert main(['--source', str(source)]) == 1
    captured = capsys.readouterr()
    assert secret not in captured.out + captured.err
    assert 'private-person' not in captured.out + captured.err
    get_settings.cache_clear()


def test_cli_unknown_commit_does_not_claim_rollback(source, configured, monkeypatch, capsys):
    from app.migration.transfer import CommitUnknown
    def fail(*args, **kwargs):
        raise CommitUnknown('Resultado do commit indeterminado; confira o destino antes de repetir')
    monkeypatch.setattr('app.scripts.migrate_sqlite.migrate', fail)
    assert main(['--source', str(source), '--apply']) == 1
    assert 'indeterminado' in capsys.readouterr().err


def test_bad_configuration_and_source_leave_failure_report(tmp_path, monkeypatch):
    monkeypatch.setenv('JWT_SECRET_KEY', 'short')
    get_settings.cache_clear()
    try:
        report = tmp_path / 'failed.json'
        assert main(['--source', str(tmp_path / 'absent.db'), '--report', str(report)]) == 1
        assert json.loads(report.read_text())['committed'] is False
    finally:
        get_settings.cache_clear()


def test_invalid_arguments_return_two():
    with pytest.raises(SystemExit) as result:
        main(['--unexpected'])
    assert result.value.code == 2


def test_stdout_failure_after_commit_does_not_deny_the_load(source, configured, tmp_path, monkeypatch, capsys):
    import builtins
    actual_print = builtins.print
    def broken_stdout(*args, **kwargs):
        if kwargs.get('file') is None:
            raise BrokenPipeError('closed output')
        return actual_print(*args, **kwargs)
    monkeypatch.setattr('builtins.print', broken_stdout)
    report = tmp_path / 'committed.json'
    assert main(['--source', str(source), '--apply', '--report', str(report)]) == 1
    error = capsys.readouterr().err
    assert 'Carga confirmada' in error
    assert 'Nenhuma carga confirmada' not in error
    assert json.loads(report.read_text())['committed'] is True
    with configured.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM companies')) == 1
