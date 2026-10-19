"""Confirm parsed payroll previews and list a company's import history."""
import asyncio
import hashlib
import hmac
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response
from starlette.datastructures import UploadFile

from app.api.routes.companies import AuthorizedCompany
from app.api.routes.payroll_preview import Previewer, read_form, run_connected
from app.core.dependencies import Database, unauthorized
from app.models import PayrollImport, User
from app.schemas.payroll_import import (
    PayrollImportCreated, PayrollImportHistoryItem, PayrollImportHistoryPage,
)
from app.services.authorization import require_company_access
from app.services.payroll_import import persist_import
from app.services.payroll_preview import COMPETENCE, build_preview
from app.services.payroll_preview_files import (
    EXTENSIONS, MAX_FILE_BYTES, PreviewInputError, safe_filename, validate_document,
)
from app.services.payroll_preview_runner import preview_runner

router = APIRouter(prefix='/api/v1/companies/{company_id}/payroll-imports', tags=['payroll-imports'])
IMPORT_MULTIPART_SCHEMA = {'requestBody': {'required': True, 'content': {'multipart/form-data': {'schema': {
    'type': 'object', 'required': ['file', 'competence', 'preview_sha256'], 'additionalProperties': False,
    'properties': {
        'file': {'type': 'string', 'format': 'binary'},
        'competence': {'type': 'string', 'pattern': r'^(0[1-9]|1[0-2])/[0-9]{4}$'},
        'preview_sha256': {'type': 'string', 'pattern': r'^[a-fA-F0-9]{64}$'},
    },
}}}}}


@router.post('', status_code=201, response_model=PayrollImportCreated,
             openapi_extra=IMPORT_MULTIPART_SCHEMA,
             responses={code: {'description': message} for code, message in {
                 400: 'Arquivo ilegível', 401: 'Sessão inválida', 403: 'Sem permissão',
                 409: 'Empresa inativa, prévia divergente ou competência já importada',
                 413: 'Limite excedido', 415: 'Formato não suportado', 422: 'Multipart ou competência inválida',
                 503: 'Leitores ocupados', 504: 'Prazo excedido',
             }.items()})
async def confirm_import(request: Request, response: Response, actor: Previewer,
                         company: AuthorizedCompany, db: Database):
    response.headers['Cache-Control'] = 'no-store'
    if company.status != 'Ativa':
        raise HTTPException(status_code=409, detail='Empresa inativa.')
    actor_id, company_id = actor.id, company.id
    db.rollback()
    form = None
    try:
        form = await read_form(request, max_fields=2)
        fields = form.multi_items()
        if len(fields) != 3 or sorted(key for key, _ in fields) != ['competence', 'file', 'preview_sha256']:
            raise PreviewInputError(422, 'Envie exatamente arquivo, competência e hash da prévia.')
        upload, competence, expected_sha256 = form['file'], form['competence'], form['preview_sha256']
        if (not isinstance(upload, UploadFile) or not isinstance(competence, str)
                or not COMPETENCE.fullmatch(competence) or not isinstance(expected_sha256, str)
                or not re.fullmatch(r'[a-fA-F0-9]{64}', expected_sha256)):
            raise PreviewInputError(422, 'Envie arquivo, competência MM/AAAA e SHA-256 hexadecimal válido.')
        filename = safe_filename(upload.filename)
        extension = Path(filename).suffix.lower()
        if extension not in EXTENSIONS:
            raise PreviewInputError(415, 'Envie um Extrato Mensal PDF, XLS ou XLSX.')
        data = await upload.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise PreviewInputError(413, 'O arquivo excede 10 MiB.')
        sha256 = hashlib.sha256(data).hexdigest()
        if not hmac.compare_digest(sha256, expected_sha256.lower()):
            raise HTTPException(status_code=409, detail='O arquivo não corresponde à prévia apresentada.')

        with TemporaryDirectory() as directory:
            path = Path(directory) / f'document{extension}'
            await asyncio.to_thread(path.write_bytes, data)
            validate_document(path, extension)
            parsed = await run_connected(request, path, extension)

        db.rollback()
        db.expire_all()
        user = db.get(User, actor_id)
        if user is None or not user.is_active:
            raise unauthorized()
        if user.role.name not in ('Administrador', 'Contador', 'Operador'):
            raise HTTPException(status_code=403, detail='Acesso negado')
        current_company = require_company_access(db, company_id, user)
        if current_company.status != 'Ativa':
            raise HTTPException(status_code=409, detail='Empresa inativa.')
        preview = build_preview(
            parsed, company_id=company_id, company_cnpj=current_company.cnpj,
            competence=competence, filename=filename, size_bytes=len(data),
            sha256=sha256, extension=extension,
        )
        if preview.status != 'ready':
            raise HTTPException(status_code=409, detail='A prévia está bloqueada ou diverge da empresa e competência selecionadas.')
        summary = preview.summary
        db.rollback()
        payroll_import = persist_import(
            db, actor_id=actor_id, company_id=company_id, competence=competence,
            filename=filename, size_bytes=len(data), sha256=sha256, statement=parsed,
        )
        response.headers['Cache-Control'] = 'no-store'
        return PayrollImportCreated(
            import_id=payroll_import.id, company_id=company_id,
            competence=payroll_import.competencia, filename=payroll_import.arquivo,
            size_bytes=payroll_import.arquivo_bytes, sha256=payroll_import.arquivo_sha256,
            imported_at=payroll_import.data_hora, employees=summary.employees,
            rubrics=summary.rubrics, totals_by_type=summary.totals_by_type,
            net_total=summary.net_total,
        )
    except PreviewInputError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message,
                            headers={'Cache-Control': 'no-store'}) from None
    finally:
        if form is not None:
            await form.close()


@router.get('', response_model=PayrollImportHistoryPage)
def list_imports(company: AuthorizedCompany, db: Database, response: Response,
                 offset: Annotated[int, Query(ge=0)] = 0,
                 limit: Annotated[int, Query(ge=1, le=100)] = 50):
    response.headers['Cache-Control'] = 'no-store'
    if company.status != 'Ativa':
        raise HTTPException(status_code=409, detail='Empresa inativa.')
    query = db.query(PayrollImport).filter(PayrollImport.company_id == company.id)
    total = query.count()
    rows = query.order_by(PayrollImport.data_hora.desc().nullslast(), PayrollImport.id.desc()) \
        .offset(offset).limit(limit).all()
    response.headers['Cache-Control'] = 'no-store'
    return PayrollImportHistoryPage(
        items=[PayrollImportHistoryItem(
            import_id=row.id, company_id=company.id, competence=row.competencia,
            filename=row.arquivo, status=row.status, imported_at=row.data_hora,
            size_bytes=row.arquivo_bytes, sha256=row.arquivo_sha256,
            employees=row.quantidade_colaboradores, rubrics=row.quantidade_rubricas,
        ) for row in rows],
        offset=offset, limit=limit, total=total,
    )
