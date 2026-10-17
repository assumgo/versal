"""Desktop 2.18 Excel reader restricted to monthly statements."""
from pathlib import Path

from .common import _cell_str
from .errors import UnsupportedLayoutError
from .extrato import parse_extrato_rows
from .files import local_document_path
from .types import ParsedStatement


def parse_excel(path: str | Path) -> ParsedStatement:
    """Read the first worksheet, preserving desktop fallback and title priority."""
    path = local_document_path(path)
    try:
        from python_calamine import load_workbook

        with load_workbook(path) as workbook:
            rows = list(workbook.get_sheet_by_index(0).iter_rows())
    except Exception:
        import pandas as pd

        frame = pd.read_excel(path, header=None, dtype=object)
        rows = frame.fillna('').values.tolist()

    flat = '\n'.join(
        ' '.join(_cell_str(value) for value in row if _cell_str(value))
        for row in rows[:120]
    ).upper()
    if 'EXTRATO MENSAL' in flat:
        return parse_extrato_rows(rows)
    if any(title in flat for title in (
        'PROVISÃO DE 13', 'PROVISAO DE 13',
        'PROVISÃO DE DÉCIMO TERCEIRO', 'PROVISAO DE DECIMO TERCEIRO',
        'PROVISÃO DE FÉRIAS', 'PROVISAO DE FERIAS',
        'DETALHAMENTO DA PROVISÃO DE FÉRIAS',
    )):
        raise UnsupportedLayoutError('Provisões ainda não são suportadas por este leitor de Extrato Mensal.')
    return parse_extrato_rows(rows)
