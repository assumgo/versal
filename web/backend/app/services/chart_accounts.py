from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ChartAccount, User
from app.repositories import chart_accounts as repository
from app.schemas.chart_accounts import ChartAccountCreate, ChartAccountUpdate
from app.services.companies import save
from app.services.employees import require_active


def create(db: Session, company_id: int, payload: ChartAccountCreate, actor: User, ip: str | None) -> ChartAccount:
    require_active(db, company_id)
    if repository.find_by_code(db, company_id, payload.conta) is not None:
        raise HTTPException(status_code=409, detail='Conta já cadastrada nesta empresa')
    values = payload.model_dump()
    values['gera_cor'] = int(payload.tipo_correntista.startswith('2'))
    row = ChartAccount(company_id=company_id, **values)
    db.add(row)
    save(db, row, actor, 'chart_account.create', 'chart_accounts', company_id, ip, values.keys())
    return row


def update(db: Session, company_id: int, account_id: int, payload: ChartAccountUpdate,
           actor: User, ip: str | None) -> ChartAccount:
    require_active(db, company_id)
    row = repository.find(db, company_id, account_id)
    values = payload.model_dump(exclude_unset=True)
    if 'tipo_correntista' in values:
        values['gera_cor'] = int(values['tipo_correntista'].startswith('2'))
    changed = {key for key, value in values.items() if getattr(row, key) != value}
    for key, value in values.items():
        setattr(row, key, value)
    save(db, row, actor, 'chart_account.update', 'chart_accounts', company_id, ip, changed)
    return row
