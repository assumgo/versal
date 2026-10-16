from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import ChartAccount


def literal_pattern(value: str) -> str:
    return '%' + value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'


def list_for_company(db: Session, company_id: int, *, q: str, offset: int,
                     limit: int, conta: str | None = None) -> dict:
    filters = [ChartAccount.company_id == company_id]
    if q:
        pattern = literal_pattern(q)
        filters.append(or_(ChartAccount.conta.ilike(pattern, escape='\\'), ChartAccount.descricao.ilike(pattern, escape='\\')))
    if conta is not None:
        filters.append(ChartAccount.conta == conta)
    return {
        'items': db.scalars(select(ChartAccount).where(*filters).order_by(
            ChartAccount.conta, ChartAccount.id).offset(offset).limit(limit)).all(),
        'total': db.scalar(select(func.count()).select_from(ChartAccount).where(*filters)),
        'offset': offset, 'limit': limit,
    }


def find(db: Session, company_id: int, account_id: int) -> ChartAccount:
    row = db.scalar(select(ChartAccount).where(ChartAccount.company_id == company_id, ChartAccount.id == account_id))
    if row is None:
        raise HTTPException(status_code=404, detail='Conta não encontrada')
    return row


def find_by_code(db: Session, company_id: int, code: str) -> ChartAccount | None:
    return db.scalar(select(ChartAccount).where(ChartAccount.company_id == company_id,
                                               ChartAccount.conta == code).order_by(ChartAccount.id).limit(1))
