from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Rubric, User
from app.repositories import chart_accounts, rubrics as repository
from app.schemas.accounting import normalize_account
from app.schemas.rubrics import RubricCreate, RubricUpdate
from app.services.companies import save
from app.services.employees import require_active


def _desktop_flags(db: Session, company_id: int, values: dict, row: Rubric | None = None) -> None:
    # Saving uses the account directly; OR and salary exceptions belong to export.
    for side in ('debito', 'credito'):
        field = f'conta_{side}'
        code = normalize_account(values.get(field, getattr(row, field, None)) or '')
        account = chart_accounts.find_by_code(db, company_id, code) if code else None
        if account is None:
            continue
        if account.utiliza_cc not in (0, 1) or account.gera_cor not in (0, 1):
            raise HTTPException(status_code=409, detail=f'Corrija as opções CC/COR da conta de {side} no plano de contas')
        values[f'{side}_gera_cc'] = account.utiliza_cc
        values[f'{side}_gera_cor'] = account.gera_cor


def create(db: Session, company_id: int, payload: RubricCreate, actor: User, ip: str | None) -> Rubric:
    require_active(db, company_id)
    if repository.find_by_code(db, company_id, payload.codigo) is not None:
        raise HTTPException(status_code=409, detail='Código de rubrica já cadastrado nesta empresa')
    values = payload.model_dump()
    _desktop_flags(db, company_id, values)
    row = Rubric(company_id=company_id, **values)
    db.add(row)
    save(db, row, actor, 'rubric.create', 'rubrics', company_id, ip, values.keys())
    return row


def update(db: Session, company_id: int, rubric_id: int, payload: RubricUpdate,
           actor: User, ip: str | None) -> Rubric:
    require_active(db, company_id)
    row = repository.find(db, company_id, rubric_id)
    values = payload.model_dump(exclude_unset=True)
    code = values.get('codigo', row.codigo)
    if code != row.codigo and repository.find_by_code(db, company_id, code) is not None:
        raise HTTPException(status_code=409, detail='Código de rubrica já cadastrado nesta empresa')
    _desktop_flags(db, company_id, values, row)
    changed = {key for key, value in values.items() if getattr(row, key) != value}
    for key, value in values.items():
        setattr(row, key, value)
    save(db, row, actor, 'rubric.update', 'rubrics', company_id, ip, changed)
    return row
