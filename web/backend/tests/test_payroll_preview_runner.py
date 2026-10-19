import asyncio
from decimal import Decimal
import json
from pathlib import Path
import sys

import pytest

from app.services.payroll_preview_files import PreviewInputError
from app.services.payroll_preview_runner import PreviewRunner

ROOT = Path(__file__).parent / 'fixtures/parser_equivalence'


@pytest.mark.asyncio
@pytest.mark.parametrize('suffix', ['pdf', 'xls', 'xlsx'])
async def test_runner_reads_real_corpus(suffix):
    result = await PreviewRunner().run(ROOT / f'extrato_{suffix}' / f'input.{suffix}', f'.{suffix}')
    expected = json.loads((ROOT / f'extrato_{suffix}' / 'expected.json').read_text())
    assert json.loads(json.dumps(result, default=str)) == expected
    assert isinstance(result['colaboradores'][0]['liquido'], Decimal)


@pytest.mark.asyncio
async def test_runner_drains_large_pipe_and_sanitizes_errors(monkeypatch):
    original = asyncio.create_subprocess_exec
    result = {'competencia': '', 'empresa': {'codigo_siagri': '', 'razao': 'A' * 100000, 'cnpj': ''},
              'tipo_importacao': 'Extrato', 'colaboradores': []}
    async def spawn(*args, **kwargs):
        return await original(sys.executable, '-c', 'import json; print(json.dumps(' + repr({'statement': result}) + '))', **kwargs)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', spawn)
    assert len((await PreviewRunner().run(ROOT, '.pdf'))['empresa']['razao']) == 100000
    async def broken(*args, **kwargs):
        return await original(sys.executable, '-c', "print('private internal exception')", **kwargs)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', broken)
    with pytest.raises(PreviewInputError) as error:
        await PreviewRunner().run(ROOT, '.pdf')
    assert error.value.status_code == 400
    assert 'private' not in str(error.value)


@pytest.mark.asyncio
async def test_timeout_cancellation_and_busy_release_processes(monkeypatch):
    original = asyncio.create_subprocess_exec
    processes = []
    async def spawn(*args, **kwargs):
        process = await original(sys.executable, '-c', 'import time; time.sleep(30)', **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', spawn)
    runner = PreviewRunner(timeout=0.3)
    tasks = [asyncio.create_task(runner.run(ROOT, '.pdf')) for _ in range(2)]
    for _ in range(100):
        if len(processes) == 2:
            break
        await asyncio.sleep(0.01)
    with pytest.raises(PreviewInputError) as error:
        await runner.run(ROOT, '.pdf')
    assert error.value.status_code == 503
    tasks[0].cancel()
    with pytest.raises(asyncio.CancelledError):
        await tasks[0]
    with pytest.raises(PreviewInputError) as error:
        await tasks[1]
    assert error.value.status_code == 504
    assert all(p.returncode is not None for p in processes)
    with pytest.raises(PreviewInputError) as error:
        await runner.run(ROOT, '.pdf')
    assert error.value.status_code == 504
    assert processes[-1].returncode is not None


@pytest.mark.asyncio
async def test_worker_sanitizes_corrupt_file(tmp_path):
    path = tmp_path / 'private-name.pdf'
    path.write_bytes(b'%PDF-broken')
    with pytest.raises(PreviewInputError) as error:
        await PreviewRunner().run(path, '.pdf')
    assert error.value.status_code == 400
    assert str(path) not in str(error.value)


@pytest.mark.asyncio
async def test_worker_rejects_provision_without_leaking_path(tmp_path):
    from openpyxl import Workbook
    path = tmp_path / 'provision.xlsx'
    workbook = Workbook()
    workbook.active.append(['PROVISÃO DE FÉRIAS'])
    workbook.save(path)
    workbook.close()
    with pytest.raises(PreviewInputError) as error:
        await PreviewRunner().run(path, '.xlsx')
    assert error.value.status_code == 415


def test_worker_enforces_result_limits(monkeypatch):
    from app.services import payroll_preview_worker as worker
    monkeypatch.setattr(worker, 'parse_excel', lambda path: {'colaboradores': [{'rubricas': []}] * 2001})
    result = worker.process_document(ROOT / 'extrato_xlsx/input.xlsx', '.xlsx')
    assert result['error']['status'] == 413
