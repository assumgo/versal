from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Rubric
from app.repositories.chart_accounts import literal_pattern


def list_for_company(db: Session, company_id: int, *, q: str, offset: int,
                     limit: int, status: str | None = None) -> dict:
    filters = [Rubric.company_id == company_id]
    if q:
        pattern = literal_pattern(q)
        filters.append(or_(Rubric.codigo.ilike(pattern, escape='\\'), Rubric.descricao.ilike(pattern, escape='\\')))
    if status is not None:
        filters.append(Rubric.status == status)
    return {
        'items': db.scalars(select(Rubric).where(*filters).order_by(
            Rubric.codigo, Rubric.id).offset(offset).limit(limit)).all(),
        'total': db.scalar(select(func.count()).select_from(Rubric).where(*filters)),
        'offset': offset, 'limit': limit,
    }


def find(db: Session, company_id: int, rubric_id: int) -> Rubric:
    row = db.scalar(select(Rubric).where(Rubric.company_id == company_id, Rubric.id == rubric_id))
    if row is None:
        raise HTTPException(status_code=404, detail='Rubrica não encontrada')
    return row


def find_by_code(db: Session, company_id: int, code: str) -> Rubric | None:
    return db.scalar(select(Rubric).where(Rubric.company_id == company_id,
                                        Rubric.codigo == code).order_by(Rubric.id).limit(1))
