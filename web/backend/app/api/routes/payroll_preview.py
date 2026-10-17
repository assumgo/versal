"""Bounded, authorized preview uploads with no database writes."""
import asyncio
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

from app.api.routes.companies import AuthorizedCompany
from app.core.dependencies import Database, require_roles, unauthorized
from app.models import User
from app.schemas.payroll_preview import PayrollPreviewResponse
from app.services.authorization import require_company_access
from app.services.payroll_preview import COMPETENCE, build_preview
from app.services.payroll_preview_files import EXTENSIONS, MAX_FILE_BYTES, PreviewInputError, safe_filename, validate_document
from app.services.payroll_preview_runner import preview_runner

router = APIRouter(prefix='/api/v1/companies/{company_id}/payroll-import-preview', tags=['payroll-preview'])
PREVIEW_ROLES = ('Administrador', 'Contador', 'Operador')
Previewer = Annotated[User, Depends(require_roles(*PREVIEW_ROLES))]
MAX_BODY_BYTES = MAX_FILE_BYTES + 64 * 1024
MULTIPART_SCHEMA = {'requestBody': {'required': True, 'content': {'multipart/form-data': {'schema': {
    'type': 'object', 'required': ['file', 'competence'], 'additionalProperties': False,
    'properties': {'file': {'type': 'string', 'format': 'binary'},
                   'competence': {'type': 'string', 'pattern': r'^(0[1-9]|1[0-2])/[0-9]{4}$'}},
}}}}}


async def read_form(request: Request):
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_BODY_BYTES:
            raise PreviewInputError(413, 'O envio excede o limite de 10 MiB e seu envelope multipart.')
        body.extend(chunk)

    async def stream():
        yield bytes(body)

    parser = None
    form = None
    try:
        if request.headers.get('content-type', '').split(';')[0].lower() != 'multipart/form-data':
            raise MultiPartException('multipart required')
        parser = MultiPartParser(request.headers, stream(), max_files=1, max_fields=1, max_part_size=64 * 1024)
        form = await parser.parse()
        return form
    except (MultiPartException, ValueError):
        raise PreviewInputError(422, 'Envie exatamente um arquivo e a competência MM/AAAA.') from None
    finally:
        if parser is not None and form is None:
            # Starlette closes these on MultiPartException, but not on cancellation.
            for file in parser._files_to_close_on_error:
                file.close()


async def run_connected(request: Request, path: Path, extension: str):
    async def disconnected():
        # The body has been fully consumed; this is the sole remaining receiver.
        # is_disconnected() uses a cancellation scope that can swallow task.cancel().
        while True:
            message = await request.receive()
            if message['type'] == 'http.disconnect':
                return

    parsing = asyncio.create_task(preview_runner.run(path, extension))
    monitor = asyncio.create_task(disconnected())
    try:
        done, _ = await asyncio.wait((parsing, monitor), return_when=asyncio.FIRST_COMPLETED)
        if monitor in done:
            raise HTTPException(status_code=499, detail='Envio cancelado.')
        return await parsing
    finally:
        for task in (parsing, monitor):
            if not task.done():
                task.cancel()
        await asyncio.shield(asyncio.gather(parsing, monitor, return_exceptions=True))


@router.post('', response_model=PayrollPreviewResponse, openapi_extra=MULTIPART_SCHEMA,
             responses={code: {'description': message} for code, message in {
                 400: 'Arquivo ilegível', 401: 'Sessão inválida', 403: 'Sem permissão', 409: 'Empresa inativa',
                 413: 'Limite excedido', 415: 'Formato não suportado', 422: 'Multipart ou competência inválida',
                 503: 'Leitores ocupados', 504: 'Prazo excedido',
             }.items()})
async def generate_preview(request: Request, response: Response, actor: Previewer,
                           company: AuthorizedCompany, db: Database):
    if company.status != 'Ativa':
        raise HTTPException(status_code=409, detail='Empresa inativa.')
    actor_id, company_id = actor.id, company.id
    # End the initial read transaction before receiving or processing the document.
    db.rollback()
    form = None
    try:
        form = await read_form(request)
        fields = form.multi_items()
        if len(fields) != 2 or sorted(key for key, _ in fields) != ['competence', 'file']:
            raise PreviewInputError(422, 'Envie exatamente um arquivo e a competência MM/AAAA.')
        upload, competence = form['file'], form['competence']
        if not isinstance(upload, UploadFile) or not isinstance(competence, str) or not COMPETENCE.fullmatch(competence):
            raise PreviewInputError(422, 'Envie um arquivo e a competência válida no formato MM/AAAA.')
        filename = safe_filename(upload.filename)
        extension = Path(filename).suffix.lower()
        if extension not in EXTENSIONS:
            raise PreviewInputError(415, 'Envie um Extrato Mensal PDF, XLS ou XLSX.')
        data = await upload.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise PreviewInputError(413, 'O arquivo excede 10 MiB.')
        with TemporaryDirectory() as directory:
            path = Path(directory) / f'document{extension}'
            await asyncio.to_thread(path.write_bytes, data)
            validate_document(path, extension)
            statement = await run_connected(request, path, extension)
        # A fresh read observes changes made while the worker was running.
        db.rollback()
        db.expire_all()
        user = db.get(User, actor_id)
        if user is None or not user.is_active:
            raise unauthorized()
        if user.role.name not in PREVIEW_ROLES:
            raise HTTPException(status_code=403, detail='Acesso negado')
        current_company = require_company_access(db, company_id, user)
        if current_company.status != 'Ativa':
            raise HTTPException(status_code=409, detail='Empresa inativa.')
        response.headers['Cache-Control'] = 'no-store'
        return build_preview(statement, company_id=company_id, company_cnpj=current_company.cnpj,
                             competence=competence, filename=filename, size_bytes=len(data),
                             sha256=hashlib.sha256(data).hexdigest(), extension=extension)
    except PreviewInputError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message,
                            headers={'Cache-Control': 'no-store'}) from None
    finally:
        if form is not None:
            await form.close()
