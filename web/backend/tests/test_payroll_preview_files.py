from pathlib import Path
import struct
from zipfile import ZipFile

import pytest

from app.services.payroll_preview_files import PreviewInputError, safe_filename, validate_document, validate_result

ROOT = Path(__file__).parent / 'fixtures/parser_equivalence'


@pytest.mark.parametrize('suffix', ['pdf', 'xls', 'xlsx'])
def test_validates_real_corpus(suffix):
    validate_document(ROOT / f'extrato_{suffix}' / f'input.{suffix}', f'.{suffix.upper()}')


@pytest.mark.parametrize('content,extension,status', [(b'', '.pdf', 400), (b'bad', '.pdf', 415),
    (b'%PDF-bad', '.xls', 415), (b'bad', '.exe', 415)])
def test_rejects_invalid_input(tmp_path, content, extension, status):
    path = tmp_path / 'input'
    path.write_bytes(content)
    with pytest.raises(PreviewInputError) as error:
        validate_document(path, extension)
    assert error.value.status_code == status


def test_zip_requires_workbook_and_bounds_declared_size(tmp_path):
    path = tmp_path / 'input.xlsx'
    with ZipFile(path, 'w') as archive:
        archive.writestr('unknown.txt', 'test')
    with pytest.raises(PreviewInputError) as error:
        validate_document(path, '.xlsx')
    assert error.value.status_code == 415
    with ZipFile(path, 'w') as archive:
        archive.writestr('[Content_Types].xml', 'test')
        archive.writestr('xl/workbook.xml', 'test')
    data = bytearray(path.read_bytes())
    pos = data.index(b'PK\x01\x02')
    struct.pack_into('<I', data, pos + 24, 50 * 1024 * 1024 + 1)
    path.write_bytes(data)
    with pytest.raises(PreviewInputError) as error:
        validate_document(path, '.xlsx')
    assert error.value.status_code == 413
    struct.pack_into('<I', data, pos + 24, 4)
    struct.pack_into('<H', data, pos + 8, 1)
    path.write_bytes(data)
    with pytest.raises(PreviewInputError) as error:
        validate_document(path, '.xlsx')
    assert error.value.status_code == 415


def test_safe_filename_never_returns_a_path():
    assert safe_filename(r'C:\private\input.xlsx') == 'input.xlsx'
    assert safe_filename('../../input.pdf') == 'input.pdf'
    assert len(safe_filename('a' * 300)) == 255


@pytest.mark.parametrize('people,rubrics', [(2001, 0), (1, 10001)])
def test_result_limits_are_not_truncated(people, rubrics):
    result = {'colaboradores': [{'rubricas': [{}] * rubrics}] * people}
    with pytest.raises(PreviewInputError) as error:
        validate_result(result)
    assert error.value.status_code == 413


def test_file_size_is_measured_from_disk(tmp_path):
    path = tmp_path / 'large.pdf'
    with path.open('wb') as stream:
        stream.write(b'%PDF-')
        stream.truncate(10 * 1024 * 1024 + 1)
    with pytest.raises(PreviewInputError) as error:
        validate_document(path, '.pdf')
    assert error.value.status_code == 413
