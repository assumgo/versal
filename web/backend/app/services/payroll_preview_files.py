"""Input boundaries shared by upload handling and isolated parsing."""
from pathlib import Path
from zipfile import BadZipFile, ZipFile

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_XLSX_BYTES = 50 * 1024 * 1024
EXTENSIONS = {'.pdf', '.xls', '.xlsx'}


class PreviewInputError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def safe_filename(original: str | None) -> str:
    return (original or 'documento').replace('\\', '/').split('/')[-1][:255] or 'documento'


def validate_document(path: Path, extension: str) -> None:
    extension = extension.lower()
    size = path.stat().st_size
    if not size:
        raise PreviewInputError(400, 'O arquivo está vazio.')
    if size > MAX_FILE_BYTES:
        raise PreviewInputError(413, 'O arquivo excede 10 MiB.')
    with path.open('rb') as stream:
        signature = stream.read(8)
    signatures = {'.pdf': b'%PDF-', '.xls': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', '.xlsx': b'PK\x03\x04'}
    if extension not in signatures or not signature.startswith(signatures[extension]):
        raise PreviewInputError(415, 'Formato ou assinatura incompatível. Envie PDF, XLS ou XLSX.')
    if extension == '.xlsx':
        try:
            with ZipFile(path) as archive:
                entries = archive.infolist()
                if sum(item.file_size for item in entries) > MAX_XLSX_BYTES:
                    raise PreviewInputError(413, 'O conteúdo XLSX excede 50 MiB descompactados.')
                names = {item.filename for item in entries}
                if any(item.flag_bits & 1 for item in entries) or not {'[Content_Types].xml', 'xl/workbook.xml'} <= names:
                    raise PreviewInputError(415, 'Envie um XLSX válido e sem criptografia.')
        except BadZipFile:
            raise PreviewInputError(400, 'Não foi possível ler o arquivo XLSX.') from None


def validate_result(statement: dict) -> None:
    people = statement['colaboradores']
    if len(people) > 2000 or sum(len(p['rubricas']) for p in people) > 10000:
        raise PreviewInputError(413, 'A prévia excede 2.000 colaboradores ou 10.000 rubricas.')
