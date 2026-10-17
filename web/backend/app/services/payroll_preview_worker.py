"""Isolated parser entry point; never imports application configuration or DB."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys

from app.parsers import parse_excel, parse_pdf, UnsupportedLayoutError
from app.services.payroll_preview_files import PreviewInputError, validate_document, validate_result


def process_document(path: Path, extension: str) -> dict:
    try:
        validate_document(path, extension)
        with redirect_stdout(io.StringIO()):
            result = (parse_pdf if extension == '.pdf' else parse_excel)(path)
        validate_result(result)
        return {'statement': result}
    except UnsupportedLayoutError:
        return {'error': {'status': 415, 'message': 'Esta prévia aceita somente Extrato Mensal, sem provisões.'}}
    except PreviewInputError as error:
        return {'error': {'status': error.status_code, 'message': error.message}}
    except Exception:
        return {'error': {'status': 400, 'message': 'Arquivo corrompido ou ilegível. Confira o documento e tente novamente.'}}


if __name__ == '__main__':
    print(json.dumps(process_document(Path(sys.argv[1]), sys.argv[2]), default=str, ensure_ascii=False))
